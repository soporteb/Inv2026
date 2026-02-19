from django import forms

from employees.models import Employee

from .models import (
    Asset,
    AssetAssignment,
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
            "station_code",
        ]


class AssetWizardStep1Form(forms.Form):
    category = forms.ModelChoiceField(queryset=None, required=True)
    ownership_type = forms.ChoiceField(choices=Asset.OwnershipType.choices, required=True)
    provider_name = forms.CharField(max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        from core.models import Category

        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.exclude(name__icontains="toner")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("ownership_type") == Asset.OwnershipType.PROVIDER and not cleaned.get("provider_name"):
            self.add_error("provider_name", "Provider name is required for provider-owned assets.")
        return cleaned


class AssetWizardStep2Form(forms.Form):
    control_patrimonial = forms.CharField(max_length=50, required=False)
    asset_tag_internal = forms.CharField(max_length=50, required=False)
    serial = forms.CharField(max_length=80, required=False)
    acquisition_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    station_code = forms.CharField(max_length=40, required=False)
    responsible_employee = forms.ModelChoiceField(queryset=Employee.objects.none(), required=True)
    location = forms.ModelChoiceField(queryset=None, required=True)
    status = forms.ModelChoiceField(queryset=None, required=True)
    observations = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, ownership_type=None, **kwargs):
        from core.models import Location, Status

        super().__init__(*args, **kwargs)
        self.ownership_type = ownership_type
        self.fields["location"].queryset = Location.objects.filter(is_active=True)
        self.fields["status"].queryset = Status.objects.filter(is_active=True)
        self.fields["responsible_employee"].queryset = Employee.objects.filter(
            worker_type__in=[Employee.WorkerType.NOMBRADO, Employee.WorkerType.CAS],
            is_active=True,
        )
        if ownership_type == Asset.OwnershipType.PROVIDER:
            self.fields["control_patrimonial"].widget = forms.HiddenInput()

    def clean_station_code(self):
        value = self.cleaned_data.get("station_code", "").strip()
        return value or ""

    def clean(self):
        cleaned = super().clean()
        ownership_type = self.ownership_type
        control = (cleaned.get("control_patrimonial") or "").strip()
        internal = (cleaned.get("asset_tag_internal") or "").strip()

        if ownership_type == Asset.OwnershipType.PROVIDER:
            if control:
                self.add_error("control_patrimonial", "Provider-owned assets cannot have control patrimonial.")
            if not internal:
                self.add_error("asset_tag_internal", "Internal code is required for provider-owned assets.")
        elif not control and not internal:
            self.add_error("asset_tag_internal", "At least one identifier is required.")

        if control and not cleaned.get("acquisition_date"):
            self.add_error("acquisition_date", "Acquisition date is required when control patrimonial is set.")

        return cleaned


class AssetWizardStep3Form(forms.Form):
    brand = forms.CharField(max_length=120, required=False)
    model = forms.CharField(max_length=120, required=False)
    host = forms.CharField(max_length=120, required=False)
    mac = forms.CharField(max_length=17, required=False)
    ip = forms.GenericIPAddressField(required=False)
    os_name = forms.CharField(max_length=120, required=False)
    antivirus_name = forms.CharField(max_length=120, required=False)
    domain = forms.CharField(max_length=120, required=False)
    dns1 = forms.CharField(max_length=120, required=False)
    dns2 = forms.CharField(max_length=120, required=False)
    processor = forms.CharField(max_length=120, required=False)
    cpu_speed = forms.CharField(max_length=120, required=False)
    ram_total_gb = forms.IntegerField(required=False, min_value=0)
    ram_slots_total = forms.IntegerField(required=False, min_value=0)
    storage_summary = forms.CharField(max_length=255, required=False)
    padlock_present = forms.BooleanField(required=False)
    associated_email = forms.EmailField(required=False)
    managed_by_text = forms.CharField(max_length=120, required=False)
    standalone_server = forms.BooleanField(required=False)


class AssetWizardStep4SensitiveForm(forms.ModelForm):
    class Meta:
        model = AssetSensitiveData
        fields = ["cpu_padlock_key", "license_secret"]
        widgets = {
            "cpu_padlock_key": forms.PasswordInput(render_value=True),
            "license_secret": forms.Textarea(attrs={"rows": 4}),
        }


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


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = AssetAssignment
        fields = ["asset", "assigned_employee", "reason"]


class ReassignmentForm(forms.ModelForm):
    class Meta:
        model = AssetAssignment
        fields = ["asset", "assigned_employee", "reason"]
        labels = {"assigned_employee": "new assigned employee"}
