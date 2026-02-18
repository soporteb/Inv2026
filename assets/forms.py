from django import forms

from .models import (
    Asset,
    ConsumableItem,
    ConsumableMovement,
    DecommissionRecord,
    MaintenanceRecord,
    ReplacementRecord,
)


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "category",
            "location",
            "status",
            "responsible_employee",
            "observations",
            "acquisition_date",
            "control_patrimonial",
            "serial",
            "asset_tag_internal",
            "ownership_type",
            "provider_name",
        ]


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = ["asset", "maintenance_type", "status", "description", "closed_at"]


class ReplacementForm(forms.ModelForm):
    class Meta:
        model = ReplacementRecord
        fields = ["asset", "replacement_asset", "reason", "replacement_date"]


class DecommissionForm(forms.ModelForm):
    class Meta:
        model = DecommissionRecord
        fields = ["asset", "reason", "decommission_date", "disposal_method", "certificate_code"]


class ConsumableItemForm(forms.ModelForm):
    class Meta:
        model = ConsumableItem
        fields = ["name", "sku", "unit", "min_stock", "is_active"]


class ConsumableMovementForm(forms.ModelForm):
    class Meta:
        model = ConsumableMovement
        fields = ["item", "movement_type", "quantity", "unit_cost", "reason", "reference"]
