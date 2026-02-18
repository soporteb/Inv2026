from django.contrib.auth.decorators import user_passes_test

from .roles import is_admin


admin_required = user_passes_test(is_admin)
