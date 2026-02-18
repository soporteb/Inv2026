from django.core.management import call_command
from django.core.management.base import BaseCommand

from core.models import Location
from employees.models import Employee


class Command(BaseCommand):
    help = "Seed demo users and employees for phase 1."

    def handle(self, *args, **options):
        call_command("create_demo_users")

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
            Employee.objects.get_or_create(
                dni=dni,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "worker_type": worker_type,
                    "email": f"{first_name.lower()}@demo.local",
                },
            )

        if Location.objects.count() == 0:
            call_command("seed_core")

        self.stdout.write(self.style.SUCCESS("seed_demo completed (phase 1 data)"))
