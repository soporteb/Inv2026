from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Location(TimeStampedModel):
    site = models.CharField(max_length=120)
    floor = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=80)
    exact_name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["exact_name"]

    def __str__(self) -> str:
        return self.exact_name

    def safe_delete(self) -> bool:
        if self.usages.exists() or self.assets.exists():
            self.is_active = False
            self.save(update_fields=["is_active", "updated_at"])
            return False
        self.delete()
        return True


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Status(TimeStampedModel):
    name = models.CharField(max_length=60, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "statuses"

    def __str__(self) -> str:
        return self.name


class AssignmentReason(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class LocationUsage(TimeStampedModel):
    """Phase 1 placeholder to test safe deletion behavior before Asset model exists."""

    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="usages")
    note = models.CharField(max_length=120, default="seed reference")
