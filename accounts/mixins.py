from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .roles import can_manage_assets, can_view_assets, is_admin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return is_admin(self.request.user)


class AssetViewRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return can_view_assets(self.request.user)


class AssetManageRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return can_manage_assets(self.request.user)
