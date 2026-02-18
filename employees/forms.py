from django import forms

from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "dni",
            "first_name",
            "last_name",
            "worker_type",
            "email",
            "phone",
            "is_active",
        ]
