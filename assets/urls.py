from django.urls import path

from .views import (
    AssignmentCreateView,
    AssignmentListView,
    AssetCreateView,
    AssetDetailView,
    AssetListView,
    AssetReportCSVView,
    AssetReportView,
    AssetUpdateView,
    AssetWizardStep1View,
    AssetWizardStep2View,
    AssetWizardStep3View,
    AssetWizardStep4View,
    ConsumableCreateView,
    ConsumableKardexView,
    ConsumableListView,
    ConsumableMovementCreateView,
    DashboardView,
    DecommissionCreateView,
    MaintenanceCreateView,
    MaintenanceListView,
    ReassignmentCreateView,
    ReplacementCreateView,
    WizardRulesPanelView,
    WizardStep2FieldsPartialView,
    WizardStep3DetailsPartialView,
    WizardStep4SensitivePartialView,
)

app_name = "assets"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", AssetListView.as_view(), name="asset_list"),
    path("create/", AssetCreateView.as_view(), name="asset_create"),
    path("new/step-1/", AssetWizardStep1View.as_view(), name="asset_new_step1"),
    path("new/step-2/", AssetWizardStep2View.as_view(), name="asset_new_step2"),
    path("new/step-3/", AssetWizardStep3View.as_view(), name="asset_new_step3"),
    path("new/step-4/", AssetWizardStep4View.as_view(), name="asset_new_step4"),
    path("new/partials/step-2-fields/", WizardStep2FieldsPartialView.as_view(), name="asset_new_partial_step2"),
    path("new/partials/step-3-details/", WizardStep3DetailsPartialView.as_view(), name="asset_new_partial_step3"),
    path("new/partials/step-4-sensitive/", WizardStep4SensitivePartialView.as_view(), name="asset_new_partial_step4"),
    path("new/partials/rules-panel/", WizardRulesPanelView.as_view(), name="asset_new_partial_rules"),
    path("<int:pk>/", AssetDetailView.as_view(), name="asset_detail"),
    path("<int:pk>/edit/", AssetUpdateView.as_view(), name="asset_edit"),

    path("assignments/", AssignmentListView.as_view(), name="assignment_list"),
    path("assignments/create/", AssignmentCreateView.as_view(), name="assignment_create"),
    path("assignments/reassign/", ReassignmentCreateView.as_view(), name="reassignment_create"),

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
