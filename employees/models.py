from django.db import models


class Employee(models.Model):
    class WorkerType(models.TextChoices):
        NOMBRADO = "NOMBRADO", "Nombrado"
        CAS = "CAS", "CAS"
        LOCADOR = "LOCADOR", "Locador"
        PRACTICANTE = "PRACTICANTE", "Practicante"

    dni = models.CharField(max_length=8, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    worker_type = models.CharField(max_length=20, choices=WorkerType.choices)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
