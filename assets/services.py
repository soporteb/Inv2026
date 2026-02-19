from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.models import AssignmentReason
from employees.models import Employee

from .models import Asset, AssetAssignment, AssetEvent


def assign_asset(*, asset: Asset, reason: AssignmentReason, assigned_employee: Employee | None, actor=None, note: str = "") -> AssetAssignment:
    """Create first/current assignment atomically. Used when asset has no active assignment."""
    with transaction.atomic():
        current = (
            AssetAssignment.objects.select_for_update()
            .filter(asset=asset, is_current=True)
            .first()
        )
        if current:
            raise ValidationError("Asset already has a current assignment. Use reassign_asset().")

        assignment = AssetAssignment.objects.create(
            asset=asset,
            assigned_employee=assigned_employee,
            reason=reason,
            is_current=True,
        )

        desc = note or (
            f"Assigned to {assigned_employee}" if assigned_employee else "Assignment set without assigned employee"
        )
        AssetEvent.objects.create(
            asset=asset,
            event_type=AssetEvent.EventType.ASSIGNED,
            description=desc,
            created_by=actor,
        )
        return assignment


def reassign_asset(*, asset: Asset, reason: AssignmentReason, new_assigned_employee: Employee | None, actor=None, note: str = "") -> AssetAssignment:
    """Close current assignment and create a new one atomically, with event trace."""
    with transaction.atomic():
        current = (
            AssetAssignment.objects.select_for_update()
            .filter(asset=asset, is_current=True)
            .first()
        )

        if current:
            current.is_current = False
            current.end_at = timezone.now()
            current.save(update_fields=["is_current", "end_at"])

        new_assignment = AssetAssignment.objects.create(
            asset=asset,
            assigned_employee=new_assigned_employee,
            reason=reason,
            is_current=True,
        )

        before = str(current.assigned_employee) if current and current.assigned_employee else "Unassigned"
        after = str(new_assigned_employee) if new_assigned_employee else "Unassigned"
        desc = note or f"Reassigned: {before} -> {after}"
        AssetEvent.objects.create(
            asset=asset,
            event_type=AssetEvent.EventType.REASSIGNED,
            description=desc,
            created_by=actor,
        )
        return new_assignment
