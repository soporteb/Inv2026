from django.urls import path

from .views import EmployeeCreateView, EmployeeListView, EmployeeUpdateView

app_name = "employees"

urlpatterns = [
    path("", EmployeeListView.as_view(), name="employee_list"),
    path("create/", EmployeeCreateView.as_view(), name="employee_create"),
    path("<int:pk>/edit/", EmployeeUpdateView.as_view(), name="employee_edit"),
]
