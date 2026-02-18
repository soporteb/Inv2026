from django.contrib.auth.models import Group

ADMIN = "ADMIN"
TECHNICIAN = "TECHNICIAN"
VIEWER = "VIEWER"
ROLE_NAMES = [ADMIN, TECHNICIAN, VIEWER]


def bootstrap_roles() -> None:
    for role in ROLE_NAMES:
        Group.objects.get_or_create(name=role)


def has_role(user, role_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=role_name).exists()


def is_admin(user) -> bool:
    return user.is_superuser or has_role(user, ADMIN)
