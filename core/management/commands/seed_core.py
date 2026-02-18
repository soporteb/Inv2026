from django.core.management.base import BaseCommand

from core.models import AssignmentReason, Category, Location, Status


class Command(BaseCommand):
    help = "Seed core catalogs."

    def handle(self, *args, **options):
        locations = [
            "Direccion Tecnica", "Secretaria", "LabStat", "Direccion Academica",
            "Direccion ejecutiva academica", "Direccion administrativa",
            "direccion ejecutiva administrativa", "datacenter", "almacen equipos informaticos",
            "almacen general", "laboratorio 1", "laboratorio 2", "laboratorio 3",
            "laboratorio 4", "cocina", "caseta de seguridad", "hall", "pasillo piso 1",
            "pasillo piso 2", "recepcion", "azotea",
        ]

        for name in locations:
            Location.objects.get_or_create(
                exact_name=name,
                defaults={"site": "Main Campus", "floor": "N/A", "type": "ROOM", "is_active": True},
            )

        for name in ["CPU", "Laptop", "Server", "Printer", "Switch", "Access Point", "Webcam", "Headphones", "Microphone", "PC Speaker", "Teleconference"]:
            Category.objects.get_or_create(name=name)

        for name in ["Operational", "In Maintenance", "Inoperative", "Decommissioned"]:
            Status.objects.get_or_create(name=name)

        for name in ["Initial assignment", "Temporary loan", "Support", "Replacement"]:
            AssignmentReason.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS("seed_core completed"))
