from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from core.models import AssignmentReason, Category, Location, Status
from employees.models import Employee


REQUIRES_CONTROL_CATEGORIES = {
    "Teleconference",
    "Projector",
    "Interactive Whiteboard",
    "Air Conditioner",
    "Biometric Clock",
    "Tablet",
    "Sound Console",
}

REQUIRES_INTERNAL_CODE_CATEGORIES = {
    "Webcam",
    "Headphones",
    "Microphone",
    "PC Speaker",
}


class Asset(models.Model):
    class OwnershipType(models.TextChoices):
        INSTITUTION = "INSTITUTION", "Institution"
        PROVIDER = "PROVIDER", "Provider"

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="assets")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="assets")
    status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name="assets")
    responsible_employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="responsible_assets")

    observations = models.TextField(blank=True)
    acquisition_date = models.DateField(null=True, blank=True)

    control_patrimonial = models.CharField(max_length=50, unique=True, null=True, blank=True)
    serial = models.CharField(max_length=80, unique=True, null=True, blank=True)
    asset_tag_internal = models.CharField(max_length=50, unique=True, null=True, blank=True)

    ownership_type = models.CharField(max_length=20, choices=OwnershipType.choices, default=OwnershipType.INSTITUTION)
    provider_name = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(control_patrimonial__isnull=False) | Q(asset_tag_internal__isnull=False),
                name="asset_identifier_required",
            ),
            models.CheckConstraint(
                check=Q(control_patrimonial__isnull=True) | Q(acquisition_date__isnull=False),
                name="asset_acquisition_date_required_with_patrimonial",
            ),
        ]

    def __str__(self) -> str:
        return self.control_patrimonial or self.asset_tag_internal or f"Asset-{self.pk}"

    def clean(self):
        errors = {}
        if not self.control_patrimonial and not self.asset_tag_internal:
            errors["asset_tag_internal"] = "At least one identifier is required (control patrimonial or internal tag)."

        if self.control_patrimonial and not self.acquisition_date:
            errors["acquisition_date"] = "Acquisition date is required when control patrimonial is set."

        if self.ownership_type == self.OwnershipType.PROVIDER:
            if not self.provider_name:
                errors["provider_name"] = "Provider name is required for provider-owned assets."
            if self.control_patrimonial:
                errors["control_patrimonial"] = "Provider-owned assets cannot have control patrimonial."

        if not self.responsible_employee_id:
            errors["responsible_employee"] = "Responsible employee is required."
        elif self.responsible_employee.worker_type not in {Employee.WorkerType.NOMBRADO, Employee.WorkerType.CAS}:
            errors["responsible_employee"] = "Responsible employee must be NOMBRADO or CAS."

        category_name = self.category.name if self.category_id else None
        if category_name in REQUIRES_CONTROL_CATEGORIES and not self.control_patrimonial:
            errors["control_patrimonial"] = f"{category_name} requires control patrimonial."

        if category_name in REQUIRES_INTERNAL_CODE_CATEGORIES and not self.asset_tag_internal:
            errors["asset_tag_internal"] = f"{category_name} requires internal code (asset_tag_internal)."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def has_padlock_key(self) -> bool:
        return hasattr(self, "sensitive_data") and bool(self.sensitive_data.cpu_padlock_key)

    @property
    def has_license(self) -> bool:
        return hasattr(self, "sensitive_data") and bool(self.sensitive_data.license_secret)


class AssetSensitiveData(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="sensitive_data")
    cpu_padlock_key = models.CharField(max_length=255, blank=True)
    license_secret = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"SensitiveData<{self.asset_id}>"

    def can_view_values(self, user) -> bool:
        return bool(user and user.is_authenticated and (user.is_superuser or user.groups.filter(name="ADMIN").exists()))

    def as_safe_dict(self, user) -> dict:
        if self.can_view_values(user):
            return {
                "cpu_padlock_key": self.cpu_padlock_key,
                "license_secret": self.license_secret,
                "has_padlock_key": bool(self.cpu_padlock_key),
                "has_license": bool(self.license_secret),
            }
        return {
            "cpu_padlock_key": None,
            "license_secret": None,
            "has_padlock_key": bool(self.cpu_padlock_key),
            "has_license": bool(self.license_secret),
        }


class AssetAssignment(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="assignments")
    assigned_employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="asset_assignments", null=True, blank=True)
    reason = models.ForeignKey(AssignmentReason, on_delete=models.PROTECT, related_name="asset_assignments")
    start_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset"],
                condition=Q(is_current=True),
                name="unique_current_assignment_per_asset",
            )
        ]

    def clean(self):
        if self.assigned_employee and self.assigned_employee.worker_type not in {
            Employee.WorkerType.NOMBRADO,
            Employee.WorkerType.CAS,
            Employee.WorkerType.LOCADOR,
            Employee.WorkerType.PRACTICANTE,
        }:
            raise ValidationError({"assigned_employee": "Assigned employee type is not allowed."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class AssetEvent(models.Model):
    class EventType(models.TextChoices):
        CREATED = "CREATED", "Created"
        ASSIGNED = "ASSIGNED", "Assigned"
        UPDATED = "UPDATED", "Updated"
        REASSIGNED = "REASSIGNED", "Reassigned"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


class AssetLicense(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="licenses")
    product_name = models.CharField(max_length=120)
    vendor = models.CharField(max_length=120, blank=True)
    seats = models.PositiveIntegerField(default=1)
    expires_on = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    @property
    def has_secret(self) -> bool:
        return self.asset.has_license


class ComputerSpecs(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="computer_specs")
    cpu_model = models.CharField(max_length=120)
    ram_gb = models.PositiveSmallIntegerField()
    storage_gb = models.PositiveIntegerField()
    os_name = models.CharField(max_length=120, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)


class PeripheralDetails(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="peripheral_details")
    brand = models.CharField(max_length=120, blank=True)
    model = models.CharField(max_length=120, blank=True)
    connectivity = models.CharField(max_length=60, blank=True)


class PrinterDetails(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="printer_details")
    print_technology = models.CharField(max_length=50, blank=True)
    ppm = models.PositiveSmallIntegerField(default=0)
    supports_duplex = models.BooleanField(default=False)


class NetworkDeviceDetails(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="network_details")
    ports = models.PositiveSmallIntegerField(default=0)
    managed = models.BooleanField(default=False)
    wifi_standard = models.CharField(max_length=50, blank=True)


class TeleconferenceDetails(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="teleconference_details")
    camera_resolution = models.CharField(max_length=50, blank=True)
    microphone_count = models.PositiveSmallIntegerField(default=0)
    speaker_power_watts = models.PositiveSmallIntegerField(default=0)


class CameraDetails(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="camera_details")
    resolution = models.CharField(max_length=50, blank=True)
    field_of_view = models.PositiveSmallIntegerField(default=0)

class MaintenanceRecord(models.Model):
    class MaintenanceType(models.TextChoices):
        PREVENTIVE = "PREVENTIVE", "Preventive"
        CORRECTIVE = "CORRECTIVE", "Corrective"

    class MaintenanceStatus(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        CLOSED = "CLOSED", "Closed"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="maintenance_records")
    maintenance_type = models.CharField(max_length=20, choices=MaintenanceType.choices)
    status = models.CharField(max_length=20, choices=MaintenanceStatus.choices, default=MaintenanceStatus.OPEN)
    description = models.TextField()
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


class ReplacementRecord(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="replacement_records")
    replacement_asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="replaced_by_records")
    reason = models.TextField()
    replacement_date = models.DateField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


class DecommissionRecord(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="decommission_record")
    reason = models.TextField()
    decommission_date = models.DateField()
    disposal_method = models.CharField(max_length=120, blank=True)
    certificate_code = models.CharField(max_length=120, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


class ConsumableItem(models.Model):
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=50, unique=True)
    unit = models.CharField(max_length=30, default="unit")
    min_stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def current_stock(self) -> int:
        inbound = sum(self.movements.filter(movement_type=ConsumableMovement.MovementType.IN).values_list("quantity", flat=True))
        outbound = sum(self.movements.filter(movement_type=ConsumableMovement.MovementType.OUT).values_list("quantity", flat=True))
        adjustments = sum(self.movements.filter(movement_type=ConsumableMovement.MovementType.ADJUSTMENT).values_list("quantity", flat=True))
        return int(inbound - outbound + adjustments)

    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.min_stock


class ConsumableMovement(models.Model):
    class MovementType(models.TextChoices):
        IN = "IN", "Ingress"
        OUT = "OUT", "Egress"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"

    item = models.ForeignKey(ConsumableItem, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reason = models.CharField(max_length=180)
    reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        errors = {}
        if self.quantity <= 0:
            errors["quantity"] = "Quantity must be greater than zero."

        if self.movement_type == self.MovementType.OUT and self.item_id:
            current = self.item.current_stock
            if self.pk:
                prev = ConsumableMovement.objects.filter(pk=self.pk).first()
                if prev and prev.movement_type == self.MovementType.OUT:
                    current += prev.quantity
            if self.quantity > current:
                errors["quantity"] = "Cannot egress more than current stock."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
