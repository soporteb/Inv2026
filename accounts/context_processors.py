from accounts.roles import can_manage_assets, is_admin


def role_flags(request):
    user = request.user
    return {
        "is_admin_user": is_admin(user),
        "can_manage_assets": can_manage_assets(user),
    }
