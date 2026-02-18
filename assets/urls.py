from django.urls import path

from .views import (
    AssetCreateView,
    AssetDetailView,
    AssetListView,
    AssetReportCSVView,
    AssetReportView,
    AssetUpdateView,
    ConsumableCreateView,
    ConsumableKardexView,
    ConsumableListView,
    ConsumableMovementCreateView,
    DashboardView,
    DecommissionCreateView,
    MaintenanceCreateView,
    MaintenanceListView,
    ReplacementCreateView,
)

app_name = "assets"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", AssetListView.as_view(), name="asset_list"),
    path("create/", AssetCreateView.as_view(), name="asset_create"),
    path("<int:pk>/", AssetDetailView.as_view(), name="asset_detail"),
    path("<int:pk>/edit/", AssetUpdateView.as_view(), name="asset_edit"),

    path("maintenance/", MaintenanceListView.as_view(), name="maintenance_list"),
    path("maintenance/create/", MaintenanceCreateView.as_view(), name="maintenance_create"),
    path("replacement/create/", ReplacementCreateView.as_view(), name="replacement_create"),
    path("decommission/create/", DecommissionCreateView.as_view(), name="decommission_create"),

    path("consumables/", ConsumableListView.as_view(), name="consumable_list"),
    path("consumables/create/", ConsumableCreateView.as_view(), name="consumable_create"),
    path("consumables/movement/create/", ConsumableMovementCreateView.as_view(), name="consumable_movement_create"),
    path("consumables/<int:pk>/kardex/", ConsumableKardexView.as_view(), name="consumable_kardex"),

    path("reports/assets/", AssetReportView.as_view(), name="asset_report"),
    path("reports/assets.csv", AssetReportCSVView.as_view(), name="asset_report_csv"),
]
