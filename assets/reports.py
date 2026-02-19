from .models import Asset


def get_asset_safe_rows():
    rows = []
    qs = Asset.objects.select_related("category", "location", "status", "responsible_employee")
    for asset in qs:
        rows.append(
            {
                "id": asset.id,
                "category": asset.category.name,
                "location": asset.location.exact_name,
                "status": asset.status.name,
                "responsible": f"{asset.responsible_employee.first_name} {asset.responsible_employee.last_name}".strip(),
                "current_assigned": _current_assigned_name(asset),
                "asset_tag_internal": asset.asset_tag_internal or "",
                "control_patrimonial": asset.control_patrimonial or "",
                "serial": asset.serial or "",
                "ownership_type": asset.ownership_type,
                "provider_name": asset.provider_name or "",
                "has_padlock_key": "Yes" if asset.has_padlock_key else "No",
                "has_license": "Yes" if asset.has_license else "No",
            }
        )
    return rows


def _current_assigned_name(asset: Asset) -> str:
    current = asset.assignments.filter(is_current=True).select_related("assigned_employee").first()
    if not current or not current.assigned_employee:
        return ""
    return f"{current.assigned_employee.first_name} {current.assigned_employee.last_name}".strip()
