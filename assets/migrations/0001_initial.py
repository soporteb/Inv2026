import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("employees", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Asset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("observations", models.TextField(blank=True)),
                ("acquisition_date", models.DateField(blank=True, null=True)),
                ("control_patrimonial", models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ("serial", models.CharField(blank=True, max_length=80, null=True, unique=True)),
                ("asset_tag_internal", models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ("ownership_type", models.CharField(choices=[("INSTITUTION", "Institution"), ("PROVIDER", "Provider")], default="INSTITUTION", max_length=20)),
                ("provider_name", models.CharField(blank=True, max_length=200, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assets", to="core.category")),
                ("location", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assets", to="core.location")),
                ("responsible_employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="responsible_assets", to="employees.employee")),
                ("status", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assets", to="core.status")),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(check=Q(control_patrimonial__isnull=False) | Q(asset_tag_internal__isnull=False), name="asset_identifier_required"),
                    models.CheckConstraint(check=Q(control_patrimonial__isnull=True) | Q(acquisition_date__isnull=False), name="asset_acquisition_date_required_with_patrimonial"),
                ]
            },
        ),
        migrations.CreateModel(
            name="AssetSensitiveData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cpu_padlock_key", models.CharField(blank=True, max_length=255)),
                ("license_secret", models.CharField(blank=True, max_length=255)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("asset", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="sensitive_data", to="assets.asset")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="AssetEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[("CREATED", "Created"), ("ASSIGNED", "Assigned"), ("UPDATED", "Updated")], max_length=30)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="assets.asset")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="AssetAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_at", models.DateTimeField(auto_now_add=True)),
                ("end_at", models.DateTimeField(blank=True, null=True)),
                ("is_current", models.BooleanField(default=True)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="assets.asset")),
                ("assigned_employee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="asset_assignments", to="employees.employee")),
                ("reason", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="asset_assignments", to="core.assignmentreason")),
            ],
        ),
    ]
