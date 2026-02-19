from django import forms

from .models import Location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["site", "floor", "type", "exact_name", "is_active"]
