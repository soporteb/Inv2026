from django.db import IntegrityError
from django.test import TestCase

from .models import Employee


class EmployeeModelTests(TestCase):
    def test_dni_must_be_unique(self):
        Employee.objects.create(dni="12345678", first_name="A", last_name="B", worker_type="CAS")
        with self.assertRaises(IntegrityError):
            Employee.objects.create(dni="12345678", first_name="C", last_name="D", worker_type="NOMBRADO")
