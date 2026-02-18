from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from accounts.roles import ROLE_NAMES, bootstrap_roles


class Command(BaseCommand):
    help = "Create demo users for local development only."

    def handle(self, *args, **options):
        bootstrap_roles()
        for role in ROLE_NAMES:
            Group.objects.get_or_create(name=role)

        users = [
            ("admin", "Admin123!", "ADMIN", True, True),
            ("tech", "Tech123!", "TECHNICIAN", False, False),
            ("viewer", "Viewer123!", "VIEWER", False, False),
        ]

        for username, password, role, is_staff, is_superuser in users:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                    "email": f"{username}@example.com",
                },
            )
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.set_password(password)
            user.save()
            user.groups.clear()
            user.groups.add(Group.objects.get(name=role))
            self.stdout.write(self.style.SUCCESS(f"Upserted demo user: {username}"))
