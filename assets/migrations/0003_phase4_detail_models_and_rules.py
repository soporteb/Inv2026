import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0002_assignment_atomic_constraints"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssetLicense",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=120)),
                ("vendor", models.CharField(blank=True, max_length=120)),
                ("seats", models.PositiveIntegerField(default=1)),
                ("expires_on", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="licenses", to="assets.asset")),
            ],
        ),
        migrations.CreateModel(
            name="CameraDetails",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("resolution", models.CharField(blank=True, max_length=50)),
                ("field_of_view", models.PositiveSmallIntegerField(default=0)),
                ("asset", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="camera_details", to="assets.asset")),
            ],
        ),
        migrations.CreateModel(
            name="ComputerSpecs",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cpu_model", models.CharField(max_length=120)),
                ("ram_gb", models.PositiveSmallIntegerField()),
                ("storage_gb", models.PositiveIntegerField()),
                ("os_name", models.CharField(blank=True, max_length=120)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("mac_address", models.CharField(blank=True, max_length=17)),
                ("asset", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="computer_specs", to="assets.asset")),
            ],
        ),
        migrations.CreateModel(
            name="NetworkDeviceDetails",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ports", models.PositiveSmallIntegerField(default=0)),
                ("managed", models.BooleanField(default=False)),
                ("wifi_standard", models.CharField(blank=True, max_length=50)),
                ("asset", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="network_details", to="assets.asset")),
            ],
        ),
        migrations.CreateModel(
            name="PeripheralDetails",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("brand", models.CharField(blank=True, max_length=120)),
                ("model", models.CharField(blank=True, max_length=120)),
                ("connectivity", models.CharField(blank=True, max_length=60)),
                ("asset", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="peripheral_details", to="assets.asset")),
            ],
        ),
        migrations.CreateModel(
            name="PrinterDetails",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("print_technology", models.CharField(blank=True, max_length=50)),
                ("ppm", models.PositiveSmallIntegerField(default=0)),
                ("supports_duplex", models.BooleanField(default=False)),
                ("asset", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="printer_details", to="assets.asset")),
            ],
        ),
        migrations.CreateModel(
            name="TeleconferenceDetails",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("camera_resolution", models.CharField(blank=True, max_length=50)),
                ("microphone_count", models.PositiveSmallIntegerField(default=0)),
                ("speaker_power_watts", models.PositiveSmallIntegerField(default=0)),
                ("asset", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="teleconference_details", to="assets.asset")),
            ],
        ),
    ]
