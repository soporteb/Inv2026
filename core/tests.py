from django.test import TestCase

from employees.models import Employee

from assets.models import Asset
from .models import Category, Location, LocationUsage, Status


class LocationDeleteSafetyTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(site="Main", floor="1", type="ROOM", exact_name="X Lab")

    def test_location_referenced_by_usage_becomes_inactive(self):
        LocationUsage.objects.create(location=self.location, note="Referenced")

        was_deleted = self.location.safe_delete()
        self.location.refresh_from_db()

        self.assertFalse(was_deleted)
        self.assertFalse(self.location.is_active)

    def test_location_referenced_by_asset_becomes_inactive(self):
        category = Category.objects.create(name="CPU")
        status = Status.objects.create(name="Operational")
        responsible = Employee.objects.create(
            dni="98765432",
            first_name="Ana",
            last_name="Rojas",
            worker_type=Employee.WorkerType.NOMBRADO,
        )
        Asset.objects.create(
            category=category,
            location=self.location,
            status=status,
            asset_tag_internal="INT-LOC-0001",
            responsible_employee=responsible,
        )

        was_deleted = self.location.safe_delete()
        self.location.refresh_from_db()

        self.assertFalse(was_deleted)
        self.assertFalse(self.location.is_active)
