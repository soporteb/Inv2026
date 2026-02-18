from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .roles import is_admin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return is_admin(self.request.user)
