import csv

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from accounts.mixins import AssetManageRequiredMixin, AssetViewRequiredMixin
from accounts.roles import is_admin

from .forms import (
    AssignmentForm,
    AssetForm,
    ConsumableItemForm,
    ConsumableMovementForm,
    DecommissionForm,
    MaintenanceForm,
    ReassignmentForm,
    ReplacementForm,
)
from .models import Asset, AssetAssignment, ConsumableItem, ConsumableMovement, DecommissionRecord, MaintenanceRecord, ReplacementRecord
from .reports import get_asset_safe_rows
from .services import assign_asset, reassign_asset


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


class AssetListView(AssetViewRequiredMixin, ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        qs = (
            Asset.objects.select_related("category", "location", "status", "responsible_employee")
            .order_by("-created_at")
        )
        if q:
            qs = qs.filter(
                Q(asset_tag_internal__icontains=q)
                | Q(control_patrimonial__icontains=q)
                | Q(serial__icontains=q)
                | Q(category__name__icontains=q)
                | Q(location__exact_name__icontains=q)
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
            assign_asset(
                asset=form.cleaned_data["asset"],
                reason=form.cleaned_data["reason"],
                assigned_employee=form.cleaned_data["assigned_employee"],
                actor=self.request.user,
            )
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
            reassign_asset(
                asset=form.cleaned_data["asset"],
                reason=form.cleaned_data["reason"],
                new_assigned_employee=form.cleaned_data["assigned_employee"],
                actor=self.request.user,
            )
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
