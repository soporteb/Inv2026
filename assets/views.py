from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from accounts.mixins import AssetManageRequiredMixin, AssetViewRequiredMixin
from accounts.roles import is_admin

from .forms import AssetForm
from .models import Asset


class DashboardView(AssetViewRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total_assets"] = Asset.objects.count()
        ctx["operational_assets"] = Asset.objects.filter(status__name="Operational").count()
        ctx["assigned_assets"] = Asset.objects.filter(assignments__is_current=True).distinct().count()
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
