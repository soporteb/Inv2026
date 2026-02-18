from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from core.models import AssignmentReason, Category, Location, Status
from employees.models import Employee


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
