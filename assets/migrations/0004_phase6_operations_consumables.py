import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0003_phase4_detail_models_and_rules"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ConsumableItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("sku", models.CharField(max_length=50, unique=True)),
                ("unit", models.CharField(default="unit", max_length=30)),
                ("min_stock", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="MaintenanceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("maintenance_type", models.CharField(choices=[("PREVENTIVE", "Preventive"), ("CORRECTIVE", "Corrective")], max_length=20)),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("IN_PROGRESS", "In Progress"), ("CLOSED", "Closed")], default="OPEN", max_length=20)),
                ("description", models.TextField()),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="maintenance_records", to="assets.asset")),
                ("performed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="DecommissionRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.TextField()),
                ("decommission_date", models.DateField()),
                ("disposal_method", models.CharField(blank=True, max_length=120)),
                ("certificate_code", models.CharField(blank=True, max_length=120)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("asset", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="decommission_record", to="assets.asset")),
            ],
        ),
        migrations.CreateModel(
            name="ConsumableMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("movement_type", models.CharField(choices=[("IN", "Ingress"), ("OUT", "Egress"), ("ADJUSTMENT", "Adjustment")], max_length=20)),
                ("quantity", models.IntegerField()),
                ("unit_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("reason", models.CharField(max_length=180)),
                ("reference", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="movements", to="assets.consumableitem")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ReplacementRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.TextField()),
                ("replacement_date", models.DateField()),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="replacement_records", to="assets.asset")),
                ("replacement_asset", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="replaced_by_records", to="assets.asset")),
            ],
        ),
    ]
