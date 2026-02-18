from django import forms

from .models import Asset


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
