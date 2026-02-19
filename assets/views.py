import csv

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView, TemplateView, UpdateView

from accounts.mixins import AssetManageRequiredMixin, AssetViewRequiredMixin
from accounts.roles import can_manage_assets, is_admin

from .forms import (
    AssignmentForm,
    AssetForm,
    AssetWizardStep1Form,
    AssetWizardStep2Form,
    AssetWizardStep3Form,
    AssetWizardStep4SensitiveForm,
    ConsumableItemForm,
    ConsumableMovementForm,
    DecommissionForm,
    MaintenanceForm,
    ReassignmentForm,
    ReplacementForm,
)
from .models import (
    Asset,
    AssetAssignment,
    AssetEvent,
    AssetSensitiveData,
    CameraDetails,
    ComputerSpecs,
    ConsumableItem,
    ConsumableMovement,
    DecommissionRecord,
    MaintenanceRecord,
    NetworkDeviceDetails,
    PeripheralDetails,
    PrinterDetails,
    ReplacementRecord,
    TeleconferenceDetails,
)
from .reports import get_asset_safe_rows
from .services import assign_asset, reassign_asset


WIZARD_SESSION_KEY = "wizard.asset"
COMPUTER_CATEGORIES = {"CPU", "Laptop", "Server"}
NETWORK_CATEGORIES = {"Switch", "Access Point", "Router"}
CAMERA_CATEGORIES = {"Security Camera", "Webcam"}
PATRIMONIAL_REQUIRED_CATEGORIES = Asset.PATRIMONIAL_REQUIRED_CATEGORIES
SENSITIVE_STEP_CATEGORIES = {"CPU", "Laptop", "Server"}


class DashboardView(AssetViewRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total_assets"] = Asset.objects.count()
        ctx["operational_assets"] = Asset.objects.filter(status__name="Operational").count()
        ctx["assigned_assets"] = Asset.objects.filter(assignments__is_current=True).distinct().count()
        ctx["open_maintenance"] = MaintenanceRecord.objects.exclude(status=MaintenanceRecord.MaintenanceStatus.CLOSED).count()
        ctx["decommissioned_assets"] = DecommissionRecord.objects.count()
        ctx["inoperative_assets"] = Asset.objects.filter(status__name="Inoperative").count()
        ctx["low_stock_items"] = [i for i in ConsumableItem.objects.all() if i.is_low_stock]
        ctx["category_counts"] = Asset.objects.values("category__name").annotate(total=Count("id")).order_by("-total")[:8]
        return ctx


class WizardManageMixin(AssetManageRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not can_manage_assets(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_wizard_data(self):
        return self.request.session.get(WIZARD_SESSION_KEY, {})

    def set_wizard_data(self, payload):
        self.request.session[WIZARD_SESSION_KEY] = payload
        self.request.session.modified = True


class AssetWizardStep1View(WizardManageMixin, FormView):
    form_class = AssetWizardStep1Form
    template_name = "assets/wizard/step1.html"


    def get_initial(self):
        data = self.get_wizard_data()
        return {"category": data.get("category_id"), "ownership_type": data.get("ownership_type"), "provider_name": data.get("provider_name")}

    def form_valid(self, form):
        data = self.get_wizard_data()
        data.update(
            {
                "step1_done": True,
                "category_id": form.cleaned_data["category"].id,
                "category_name": form.cleaned_data["category"].name,
                "ownership_type": form.cleaned_data["ownership_type"],
                "provider_name": form.cleaned_data.get("provider_name", ""),
            }
        )
        self.set_wizard_data(data)
        return redirect("assets:asset_new_step2")


class AssetWizardStep2View(WizardManageMixin, FormView):
    form_class = AssetWizardStep2Form
    template_name = "assets/wizard/step2.html"

    def dispatch(self, request, *args, **kwargs):
        if not self.get_wizard_data().get("step1_done"):
            return redirect("assets:asset_new_step1")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        data = self.get_wizard_data()
        kwargs["ownership_type"] = data.get("ownership_type")
        return kwargs

    def get_initial(self):
        data = self.get_wizard_data()
        return data.get("step2", {})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        data = self.get_wizard_data()
        category_name = data.get("category_name")
        ownership = data.get("ownership_type")
        ctx["rules"] = {
            "patrimonial_allowed": ownership != Asset.OwnershipType.PROVIDER,
            "patrimonial_required": category_name in PATRIMONIAL_REQUIRED_CATEGORIES,
            "internal_required": ownership == Asset.OwnershipType.PROVIDER or category_name in Asset.INTERNAL_REQUIRED_CATEGORIES,
            "acquisition_required": True,
            "step4_required": is_admin(self.request.user) and category in SENSITIVE_STEP_CATEGORIES,
        }
        return ctx

    def form_valid(self, form):
        data = self.get_wizard_data()
        step2_data = dict(form.cleaned_data)
        acquisition_date = step2_data.get("acquisition_date")
        step2_data["acquisition_date"] = acquisition_date.isoformat() if acquisition_date else ""
        step2_data["responsible_employee"] = form.cleaned_data["responsible_employee"].id
        step2_data["location"] = form.cleaned_data["location"].id
        step2_data["status"] = form.cleaned_data["status"].id

        data["step2_done"] = True
        data["step2"] = step2_data
        self.set_wizard_data(data)
        return redirect("assets:asset_new_step3")


class AssetWizardStep3View(WizardManageMixin, FormView):
    form_class = AssetWizardStep3Form
    template_name = "assets/wizard/step3.html"

    def dispatch(self, request, *args, **kwargs):
        data = self.get_wizard_data()
        if not data.get("step1_done"):
            return redirect("assets:asset_new_step1")
        if not data.get("step2_done"):
            return redirect("assets:asset_new_step2")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["category_name"] = self.get_wizard_data().get("category_name")
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["category_name"] = self.get_wizard_data().get("category_name")
        return ctx

    def form_valid(self, form):
        data = self.get_wizard_data()
        data["step3_done"] = True
        data["step3"] = form.cleaned_data
        self.set_wizard_data(data)
        if is_admin(self.request.user) and data.get("category_name") in SENSITIVE_STEP_CATEGORIES:
            return redirect("assets:asset_new_step4")
        try:
            self._finish_create_asset(data, sensitive_payload={})
        except ValidationError as exc:
            messages.error(self.request, exc.message_dict.get("station_code", ["Validation error while creating asset."])[0])
            return redirect("assets:asset_new_step2")
        return redirect("assets:asset_list")

    def _finish_create_asset(self, data, sensitive_payload):
        with transaction.atomic():
            step2 = data["step2"]
            asset = Asset.objects.create(
                category_id=data["category_id"],
                ownership_type=data["ownership_type"],
                provider_name=data.get("provider_name") or None,
                control_patrimonial=step2.get("control_patrimonial") or None,
                asset_tag_internal=step2.get("asset_tag_internal") or None,
                serial=step2.get("serial") or None,
                acquisition_date=step2.get("acquisition_date") or None,
                station_code=step2.get("station_code") or None,
                responsible_employee_id=step2["responsible_employee"],
                location_id=step2["location"],
                status_id=step2["status"],
                observations=step2.get("observations") or "",
            )
            self._create_details(asset, data.get("step3", {}), data.get("category_name"))
            if sensitive_payload:
                AssetSensitiveData.objects.update_or_create(asset=asset, defaults={**sensitive_payload, "updated_by": self.request.user})
            AssetEvent.objects.create(asset=asset, event_type=AssetEvent.EventType.CREATED, created_by=self.request.user, description=f"Created {asset.public_id}")
        self.request.session.pop(WIZARD_SESSION_KEY, None)

    @staticmethod
    def _create_details(asset, payload, category_name):
        if category_name in COMPUTER_CATEGORIES:
            ComputerSpecs.objects.create(
                asset=asset,
                cpu_model=payload.get("processor") or payload.get("model") or "N/A",
                ram_gb=payload.get("ram_total_gb") or 0,
                storage_gb=0,
                os_name=payload.get("os_name") or "",
                ip_address=payload.get("ip") or None,
                mac_address=payload.get("mac") or "",
            )
        elif category_name in {"Monitor", "Keyboard", "Teclado", "Webcam", "Headphones", "Microphone", "PC Speaker", "Projector", "Interactive Whiteboard", "Air Conditioner", "Biometric Clock", "Tablet", "Sound Console"}:
            PeripheralDetails.objects.create(asset=asset, brand=payload.get("brand") or "", model=payload.get("model") or "")
        elif category_name == "Printer":
            PrinterDetails.objects.create(asset=asset, print_technology=payload.get("brand") or "", ppm=0)
        elif category_name in NETWORK_CATEGORIES:
            NetworkDeviceDetails.objects.create(asset=asset, managed=bool(payload.get("managed_by_text")), wifi_standard="")
        elif category_name == "Teleconference":
            TeleconferenceDetails.objects.create(asset=asset)
        elif category_name == "Security Camera":
            CameraDetails.objects.create(asset=asset)


class AssetWizardStep4View(AssetWizardStep3View):
    form_class = AssetWizardStep4SensitiveForm
    template_name = "assets/wizard/step4.html"

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied
        data = self.get_wizard_data()
        if not data.get("step3_done"):
            return redirect("assets:asset_new_step3")
        if data.get("category_name") not in SENSITIVE_STEP_CATEGORIES:
            return redirect("assets:asset_new_step3")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return FormView.get_form_kwargs(self)

    def get_initial(self):
        return self.get_wizard_data().get("step4", {})

    def form_valid(self, form):
        data = self.get_wizard_data()
        payload = {"cpu_padlock_key": form.cleaned_data.get("cpu_padlock_key", ""), "license_secret": form.cleaned_data.get("license_secret", "")}
        data["step4"] = payload
        self.set_wizard_data(data)
        try:
            self._finish_create_asset(data, sensitive_payload=payload)
        except ValidationError as exc:
            messages.error(self.request, exc.message_dict.get("station_code", ["Validation error while creating asset."])[0])
            return redirect("assets:asset_new_step2")
        return redirect("assets:asset_list")


class WizardRulesPanelView(WizardManageMixin, TemplateView):
    template_name = "assets/wizard/partials/rules_panel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        category = self.request.GET.get("category", "")
        ownership = self.request.GET.get("ownership", "")
        ctx["rules"] = {
            "patrimonial_allowed": ownership != Asset.OwnershipType.PROVIDER,
            "patrimonial_required": category in PATRIMONIAL_REQUIRED_CATEGORIES,
            "internal_required": ownership == Asset.OwnershipType.PROVIDER or category in Asset.INTERNAL_REQUIRED_CATEGORIES,
            "acquisition_required": True,
            "step4_required": is_admin(self.request.user) and category in SENSITIVE_STEP_CATEGORIES,
        }
        return ctx


class WizardStep2FieldsPartialView(WizardManageMixin, TemplateView):
    template_name = "assets/wizard/partials/step2_fields.html"


class WizardStep3DetailsPartialView(WizardManageMixin, TemplateView):
    template_name = "assets/wizard/partials/step3_details.html"


class WizardStep4SensitivePartialView(WizardManageMixin, TemplateView):
    template_name = "assets/wizard/partials/step4_sensitive.html"

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AssetListView(AssetViewRequiredMixin, ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        qs = Asset.objects.select_related("category", "location", "status", "responsible_employee").order_by("-created_at")
        if q:
            qs = qs.filter(
                Q(asset_tag_internal__icontains=q)
                | Q(control_patrimonial__icontains=q)
                | Q(serial__icontains=q)
                | Q(category__name__icontains=q)
                | Q(location__exact_name__icontains=q)
                | Q(public_id__icontains=q)
            )
        return qs

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["assets/partials/asset_table.html"]
        return [self.template_name]


class AssetDetailView(AssetViewRequiredMixin, DetailView):
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        asset = self.object
        sensitive = getattr(asset, "sensitive_data", None)
        if sensitive:
            ctx["sensitive"] = sensitive.as_safe_dict(self.request.user)
        else:
            ctx["sensitive"] = {"cpu_padlock_key": None, "license_secret": None, "has_padlock_key": False, "has_license": False}
        ctx["is_admin"] = is_admin(self.request.user)
        ctx["current_assignment"] = asset.assignments.filter(is_current=True).select_related("assigned_employee").first()
        ctx["maintenance_records"] = asset.maintenance_records.order_by("-opened_at")[:5]
        ctx["replacement_records"] = asset.replacement_records.order_by("-replacement_date")[:5]
        ctx["decommission_record"] = getattr(asset, "decommission_record", None)
        return ctx


class AssetCreateView(AssetManageRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = "assets/asset_form.html"
    success_url = reverse_lazy("assets:asset_list")


class AssetUpdateView(AssetManageRequiredMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = "assets/asset_form.html"
    success_url = reverse_lazy("assets:asset_list")


class AssignmentListView(AssetViewRequiredMixin, ListView):
    model = AssetAssignment
    template_name = "assets/assignment_list.html"
    context_object_name = "assignments"

    def get_queryset(self):
        return AssetAssignment.objects.select_related("asset", "assigned_employee", "reason").order_by("-start_at")


class AssignmentCreateView(AssetManageRequiredMixin, CreateView):
    model = AssetAssignment
    form_class = AssignmentForm
    template_name = "assets/assignment_form.html"
    success_url = reverse_lazy("assets:assignment_list")

    def form_valid(self, form):
        try:
            assign_asset(asset=form.cleaned_data["asset"], reason=form.cleaned_data["reason"], assigned_employee=form.cleaned_data["assigned_employee"], actor=self.request.user)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Assignment created.")
        return HttpResponseRedirect(str(self.success_url))


class ReassignmentCreateView(AssetManageRequiredMixin, CreateView):
    model = AssetAssignment
    form_class = ReassignmentForm
    template_name = "assets/reassignment_form.html"
    success_url = reverse_lazy("assets:assignment_list")

    def form_valid(self, form):
        try:
            reassign_asset(asset=form.cleaned_data["asset"], reason=form.cleaned_data["reason"], new_assigned_employee=form.cleaned_data["assigned_employee"], actor=self.request.user)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "Asset reassigned.")
        return HttpResponseRedirect(str(self.success_url))


class MaintenanceListView(AssetViewRequiredMixin, ListView):
    model = MaintenanceRecord
    template_name = "assets/maintenance_list.html"
    context_object_name = "records"


class MaintenanceCreateView(AssetManageRequiredMixin, CreateView):
    model = MaintenanceRecord
    form_class = MaintenanceForm
    template_name = "assets/maintenance_form.html"
    success_url = reverse_lazy("assets:maintenance_list")

    def form_valid(self, form):
        form.instance.performed_by = self.request.user
        return super().form_valid(form)


class ReplacementCreateView(AssetManageRequiredMixin, CreateView):
    model = ReplacementRecord
    form_class = ReplacementForm
    template_name = "assets/replacement_form.html"
    success_url = reverse_lazy("assets:asset_list")

    def form_valid(self, form):
        form.instance.approved_by = self.request.user
        return super().form_valid(form)


class DecommissionCreateView(AssetManageRequiredMixin, CreateView):
    model = DecommissionRecord
    form_class = DecommissionForm
    template_name = "assets/decommission_form.html"
    success_url = reverse_lazy("assets:asset_list")

    def form_valid(self, form):
        form.instance.approved_by = self.request.user
        return super().form_valid(form)


class ConsumableListView(AssetViewRequiredMixin, ListView):
    model = ConsumableItem
    template_name = "assets/consumable_list.html"
    context_object_name = "items"


class ConsumableCreateView(AssetManageRequiredMixin, CreateView):
    model = ConsumableItem
    form_class = ConsumableItemForm
    template_name = "assets/consumable_form.html"
    success_url = reverse_lazy("assets:consumable_list")


class ConsumableMovementCreateView(AssetManageRequiredMixin, CreateView):
    model = ConsumableMovement
    form_class = ConsumableMovementForm
    template_name = "assets/consumable_movement_form.html"
    success_url = reverse_lazy("assets:consumable_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ConsumableKardexView(AssetViewRequiredMixin, DetailView):
    model = ConsumableItem
    template_name = "assets/consumable_kardex.html"
    context_object_name = "item"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["movements"] = self.object.movements.select_related("created_by")[:100]
        return ctx


class AssetReportView(AssetViewRequiredMixin, TemplateView):
    template_name = "assets/report_assets.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rows"] = get_asset_safe_rows()
        return ctx


class AssetReportCSVView(AssetViewRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        rows = get_asset_safe_rows()
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="asset_report_safe.csv"'
        writer = csv.DictWriter(response, fieldnames=list(rows[0].keys()) if rows else [
            "id", "category", "location", "status", "responsible", "current_assigned", "asset_tag_internal",
            "control_patrimonial", "serial", "ownership_type", "provider_name", "has_padlock_key", "has_license"
        ])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return response
