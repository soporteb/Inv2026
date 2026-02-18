from datetime import date, timedelta
import random

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from assets.models import Asset, AssetAssignment, AssetEvent, AssetSensitiveData
from assets.services import assign_asset, reassign_asset
from core.models import AssignmentReason, Category, Location, Status
from employees.models import Employee


class Command(BaseCommand):
    help = "Seed demo users, employees, assets, assignments and events for phase 3."

    def handle(self, *args, **options):
        call_command("create_demo_users")
        call_command("seed_core")

        employees = [
            ("70000001", "Ana", "Rojas", "NOMBRADO"),
            ("70000002", "Luis", "Paredes", "NOMBRADO"),
            ("70000003", "Marina", "Soto", "NOMBRADO"),
            ("70000004", "Carlos", "Diaz", "CAS"),
            ("70000005", "Brenda", "Salas", "CAS"),
            ("70000006", "Jose", "Nina", "CAS"),
            ("70000007", "Pedro", "Neyra", "LOCADOR"),
            ("70000008", "Diana", "Gamarra", "LOCADOR"),
            ("70000009", "Iris", "Zevallos", "PRACTICANTE"),
            ("70000010", "Raul", "Tello", "PRACTICANTE"),
        ]
        for dni, first_name, last_name, worker_type in employees:
            Employee.objects.update_or_create(
                dni=dni,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "worker_type": worker_type,
                    "email": f"{first_name.lower()}@demo.local",
                },
            )

        responsibles = list(Employee.objects.filter(worker_type__in=[Employee.WorkerType.NOMBRADO, Employee.WorkerType.CAS]))
        assignables = list(Employee.objects.all())
        locations = list(Location.objects.filter(is_active=True))
        status_operational = Status.objects.get(name="Operational")
        status_maintenance = Status.objects.get(name="In Maintenance")
        reason_initial = AssignmentReason.objects.get(name="Initial assignment")

        plan = [
            ("CPU", 10),
            ("Laptop", 5),
            ("Server", 2),
            ("Printer", 4),
            ("Switch", 3),
            ("Access Point", 3),
            ("Webcam", 1),
            ("Headphones", 1),
            ("Microphone", 1),
            ("PC Speaker", 1),
            ("Teleconference", 2),
        ]

        assets = []
        sequence = 1
        for category_name, amount in plan:
            category = Category.objects.get(name=category_name)
            for i in range(amount):
                internal = f"INT-{category_name[:3].upper()}-{sequence:04d}"
                control = None
                acq = None

                if category_name == "Teleconference":
                    control = f"CP-TELE-{sequence:04d}"
                    acq = date.today() - timedelta(days=300 + i)
                elif category_name in {"Server", "Switch"}:
                    control = f"CP-{category_name[:3].upper()}-{sequence:04d}"
                    acq = date.today() - timedelta(days=500 + i)

                asset, _ = Asset.objects.update_or_create(
                    asset_tag_internal=internal,
                    defaults={
                        "category": category,
                        "location": random.choice(locations),
                        "status": status_operational if i % 4 else status_maintenance,
                        "observations": f"Demo {category_name} asset {sequence}",
                        "acquisition_date": acq,
                        "control_patrimonial": control,
                        "serial": f"SN-{category_name[:3].upper()}-{sequence:05d}",
                        "ownership_type": Asset.OwnershipType.INSTITUTION,
                        "provider_name": None,
                        "responsible_employee": random.choice(responsibles),
                    },
                )

                if i % 3 == 0:
                    AssetSensitiveData.objects.update_or_create(
                        asset=asset,
                        defaults={
                            "cpu_padlock_key": f"PAD-{sequence:04d}" if category_name in {"CPU", "Laptop"} else "",
                            "license_secret": f"LIC-{sequence:04d}" if category_name in {"CPU", "Laptop", "Server"} else "",
                        },
                    )

                AssetEvent.objects.get_or_create(
                    asset=asset,
                    event_type=AssetEvent.EventType.CREATED,
                    description="Asset created via seed_demo",
                )

                assets.append(asset)
                sequence += 1

        # Create current assignments and reassignment history (Phase 3)
        lab_names = {"laboratorio 1", "laboratorio 2", "laboratorio 3", "laboratorio 4"}
        initially_assigned_assets = []
        for idx, asset in enumerate(assets[:20]):
            if asset.location.exact_name.lower() in lab_names and idx % 2 == 0:
                continue
            assigned = random.choice(assignables)
            assign_asset(asset=asset, reason=reason_initial, assigned_employee=assigned, note=f"Initial assignment to {assigned}")
            initially_assigned_assets.append(asset)

        reassignment_reason = AssignmentReason.objects.get(name="Replacement")
        for asset in initially_assigned_assets[:8]:
            next_employee = random.choice(assignables)
            reassign_asset(
                asset=asset,
                reason=reassignment_reason,
                new_assigned_employee=next_employee,
                note=f"Reassigned during seed to {next_employee}",
            )

        User = get_user_model()
        self.stdout.write(self.style.SUCCESS(f"Users: {User.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Employees: {Employee.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Assets: {Asset.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Assignments: {AssetAssignment.objects.count()}"))
        self.stdout.write(self.style.SUCCESS("seed_demo completed (phase 3 data)"))
