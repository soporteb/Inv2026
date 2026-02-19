from django.db import migrations, models
from django.utils import timezone


def fill_registered_at(apps, schema_editor):
    Asset = apps.get_model("assets", "Asset")
    Asset.objects.filter(registered_at__isnull=True).update(registered_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0005_phase7_asset_wizard_fields"),
    ]

    operations = [
        migrations.RunPython(fill_registered_at, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="asset",
            name="registered_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
