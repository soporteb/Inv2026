from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin

from .forms import EmployeeForm
from .models import Employee


class EmployeeListView(AdminRequiredMixin, ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"


class EmployeeCreateView(AdminRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employees:employee_list")


class EmployeeUpdateView(AdminRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employees:employee_list")
