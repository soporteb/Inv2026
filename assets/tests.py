from datetime import date

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from core.models import AssignmentReason, Category, Location, Status
from employees.models import Employee

from .models import Asset, AssetAssignment, AssetEvent, AssetSensitiveData
from .services import assign_asset, reassign_asset


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


class AssignmentFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Switch")
        self.location = Location.objects.create(site="Main", floor="3", type="ROOM", exact_name="Datacenter")
        self.status = Status.objects.create(name="In Maintenance")
        self.reason_initial = AssignmentReason.objects.create(name="Temporary loan")
        self.reason_reassign = AssignmentReason.objects.create(name="Replacement")

        self.responsible = Employee.objects.create(dni="55555555", first_name="Luis", last_name="Paredes", worker_type=Employee.WorkerType.CAS)
        self.assignee1 = Employee.objects.create(dni="66666666", first_name="Diana", last_name="Gamarra", worker_type=Employee.WorkerType.LOCADOR)
        self.assignee2 = Employee.objects.create(dni="77777777", first_name="Iris", last_name="Zevallos", worker_type=Employee.WorkerType.PRACTICANTE)

        self.asset = Asset.objects.create(
            category=self.category,
            location=self.location,
            status=self.status,
            asset_tag_internal="INT-SWI-9000",
            responsible_employee=self.responsible,
        )

    def test_assign_asset_creates_current_assignment_and_event(self):
        assignment = assign_asset(asset=self.asset, reason=self.reason_initial, assigned_employee=self.assignee1)
        self.assertTrue(assignment.is_current)
        self.assertEqual(AssetAssignment.objects.filter(asset=self.asset, is_current=True).count(), 1)
        self.assertTrue(AssetEvent.objects.filter(asset=self.asset, event_type=AssetEvent.EventType.ASSIGNED).exists())

    def test_reassign_asset_closes_previous_and_creates_new_current(self):
        first = assign_asset(asset=self.asset, reason=self.reason_initial, assigned_employee=self.assignee1)
        second = reassign_asset(asset=self.asset, reason=self.reason_reassign, new_assigned_employee=self.assignee2)

        first.refresh_from_db()
        self.assertFalse(first.is_current)
        self.assertIsNotNone(first.end_at)
        self.assertTrue(second.is_current)
        self.assertEqual(second.assigned_employee, self.assignee2)
        self.assertEqual(AssetAssignment.objects.filter(asset=self.asset, is_current=True).count(), 1)
        self.assertTrue(AssetEvent.objects.filter(asset=self.asset, event_type=AssetEvent.EventType.REASSIGNED).exists())

    def test_unique_current_assignment_constraint(self):
        assign_asset(asset=self.asset, reason=self.reason_initial, assigned_employee=self.assignee1)
        with self.assertRaises((ValidationError, IntegrityError)):
            AssetAssignment.objects.create(
                asset=self.asset,
                assigned_employee=self.assignee2,
                reason=self.reason_initial,
                is_current=True,
            )


class Phase4CategoryRuleTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(site="Main", floor="1", type="ROOM", exact_name="Aula 01")
        self.status = Status.objects.create(name="Operational")
        self.responsible = Employee.objects.create(
            dni="88888888", first_name="Marina", last_name="Soto", worker_type=Employee.WorkerType.NOMBRADO
        )

    def _mk_category(self, name: str):
        return Category.objects.create(name=name)

    def test_teleconference_requires_control_patrimonial(self):
        category = self._mk_category("Teleconference")
        asset = Asset(
            category=category,
            location=self.location,
            status=self.status,
            asset_tag_internal="INT-TEL-001",
            responsible_employee=self.responsible,
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_projector_requires_control_patrimonial(self):
        category = self._mk_category("Projector")
        asset = Asset(
            category=category,
            location=self.location,
            status=self.status,
            asset_tag_internal="INT-PRO-001",
            responsible_employee=self.responsible,
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_webcam_requires_internal_code(self):
        category = self._mk_category("Webcam")
        asset = Asset(
            category=category,
            location=self.location,
            status=self.status,
            control_patrimonial="CP-WEBCAM-1",
            acquisition_date=date.today(),
            responsible_employee=self.responsible,
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_required_control_category_passes_with_control(self):
        category = self._mk_category("Sound Console")
        asset = Asset(
            category=category,
            location=self.location,
            status=self.status,
            asset_tag_internal="INT-SOU-001",
            control_patrimonial="CP-SOU-1",
            acquisition_date=date.today(),
            responsible_employee=self.responsible,
        )
        asset.full_clean()

from .models import ConsumableItem, ConsumableMovement
from .reports import get_asset_safe_rows


class Phase6ConsumablesAndReportsTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Printer")
        self.location = Location.objects.create(site="Main", floor="1", type="ROOM", exact_name="Warehouse")
        self.status = Status.objects.create(name="Operational")
        self.reason = AssignmentReason.objects.create(name="Support")
        self.responsible = Employee.objects.create(dni="99999999", first_name="Carlos", last_name="Diaz", worker_type=Employee.WorkerType.CAS)
        self.asset = Asset.objects.create(
            category=self.category,
            location=self.location,
            status=self.status,
            asset_tag_internal="INT-PRN-001",
            responsible_employee=self.responsible,
        )
        AssetSensitiveData.objects.create(asset=self.asset, cpu_padlock_key="PAD-HIDDEN", license_secret="LIC-HIDDEN")

    def test_consumable_out_cannot_exceed_stock(self):
        item = ConsumableItem.objects.create(name="Toner", sku="TON-01", min_stock=2)
        ConsumableMovement.objects.create(item=item, movement_type=ConsumableMovement.MovementType.IN, quantity=5, reason="Initial stock")
        with self.assertRaises(ValidationError):
            ConsumableMovement.objects.create(item=item, movement_type=ConsumableMovement.MovementType.OUT, quantity=8, reason="Usage")

    def test_safe_report_rows_do_not_include_sensitive_values(self):
        rows = get_asset_safe_rows()
        self.assertGreaterEqual(len(rows), 1)
        row = rows[0]
        self.assertIn("has_padlock_key", row)
        self.assertIn("has_license", row)
        self.assertNotIn("cpu_padlock_key", row)
        self.assertNotIn("license_secret", row)
