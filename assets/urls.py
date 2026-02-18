from django.urls import path

from .views import AssetCreateView, AssetDetailView, AssetListView, AssetUpdateView, DashboardView

app_name = "assets"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", AssetListView.as_view(), name="asset_list"),
    path("create/", AssetCreateView.as_view(), name="asset_create"),
    path("<int:pk>/", AssetDetailView.as_view(), name="asset_detail"),
    path("<int:pk>/edit/", AssetUpdateView.as_view(), name="asset_edit"),
]
