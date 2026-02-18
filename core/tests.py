from django.test import TestCase

from .models import Location, LocationUsage


class LocationDeleteSafetyTests(TestCase):
    def test_location_referenced_becomes_inactive(self):
        location = Location.objects.create(site="Main", floor="1", type="ROOM", exact_name="X Lab")
        LocationUsage.objects.create(location=location, note="Referenced")

        was_deleted = location.safe_delete()
        location.refresh_from_db()

        self.assertFalse(was_deleted)
        self.assertFalse(location.is_active)
