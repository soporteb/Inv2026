from datetime import date

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import AssignmentReason, Category, Location, Status
from employees.models import Employee

from .models import Asset, AssetSensitiveData


class AssetRulesTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="CPU")
        self.location = Location.objects.create(site="Main", floor="1", type="ROOM", exact_name="Direction")
        self.status = Status.objects.create(name="Operational")
        AssignmentReason.objects.create(name="Initial assignment")

        self.nombrado = Employee.objects.create(dni="11111111", first_name="Nom", last_name="Brado", worker_type=Employee.WorkerType.NOMBRADO)
        self.cas = Employee.objects.create(dni="22222222", first_name="C", last_name="As", worker_type=Employee.WorkerType.CAS)
        self.locador = Employee.objects.create(dni="33333333", first_name="Lo", last_name="Cador", worker_type=Employee.WorkerType.LOCADOR)

    def test_responsible_required(self):
        asset = Asset(
            category=self.category,
            location=self.location,
            status=self.status,
            asset_tag_internal="INT-0001",
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_responsible_must_be_nombrado_or_cas(self):
        asset = Asset(
            category=self.category,
            location=self.location,
            status=self.status,
            asset_tag_internal="INT-0002",
            responsible_employee=self.locador,
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_identifier_rule(self):
        asset = Asset(
            category=self.category,
            location=self.location,
            status=self.status,
            responsible_employee=self.nombrado,
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_acquisition_required_when_control_present(self):
        asset = Asset(
            category=self.category,
            location=self.location,
            status=self.status,
            control_patrimonial="CP-1",
            responsible_employee=self.cas,
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_provider_owned_rules(self):
        asset = Asset(
            category=self.category,
            location=self.location,
            status=self.status,
            ownership_type=Asset.OwnershipType.PROVIDER,
            asset_tag_internal="INT-0003",
            control_patrimonial="CP-2",
            acquisition_date=date.today(),
            responsible_employee=self.nombrado,
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()


class SensitiveDataVisibilityTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Laptop")
        self.location = Location.objects.create(site="Main", floor="2", type="ROOM", exact_name="Secretaria")
        self.status = Status.objects.create(name="Operational")
        self.responsible = Employee.objects.create(dni="44444444", first_name="Ana", last_name="Rojas", worker_type=Employee.WorkerType.NOMBRADO)

        self.asset = Asset.objects.create(
            category=self.category,
            location=self.location,
            status=self.status,
            asset_tag_internal="INT-0004",
            responsible_employee=self.responsible,
        )
        self.sensitive = AssetSensitiveData.objects.create(asset=self.asset, cpu_padlock_key="PAD-XYZ", license_secret="LIC-XYZ")

        self.admin = User.objects.create_user(username="admin_test", password="x")
        self.viewer = User.objects.create_user(username="viewer_test", password="x")
        admin_group, _ = Group.objects.get_or_create(name="ADMIN")
        self.admin.groups.add(admin_group)

    def test_non_admin_cannot_access_sensitive_values(self):
        payload = self.sensitive.as_safe_dict(self.viewer)
        self.assertIsNone(payload["cpu_padlock_key"])
        self.assertIsNone(payload["license_secret"])
        self.assertTrue(payload["has_padlock_key"])
        self.assertTrue(payload["has_license"])

    def test_admin_can_access_sensitive_values(self):
        payload = self.sensitive.as_safe_dict(self.admin)
        self.assertEqual(payload["cpu_padlock_key"], "PAD-XYZ")
        self.assertEqual(payload["license_secret"], "LIC-XYZ")
