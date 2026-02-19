from django.db import migrations, models
from django.db.models import Q




def populate_public_id(apps, schema_editor):
    Asset = apps.get_model("assets", "Asset")
    for asset in Asset.objects.order_by("id"):
        if not asset.public_id:
            asset.public_id = f"ASSET-{asset.id:08d}"
            asset.save(update_fields=["public_id"])

def ownership_institution_to_inei(apps, schema_editor):
    Asset = apps.get_model("assets", "Asset")
    Asset.objects.filter(ownership_type="INSTITUTION").update(ownership_type="INEI")


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0004_phase6_operations_consumables"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="public_id",
            field=models.CharField(blank=True, editable=False, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="asset",
            name="registered_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="asset",
            name="station_code",
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.RunPython(populate_public_id, migrations.RunPython.noop),
        migrations.RunPython(ownership_institution_to_inei, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="asset",
            name="ownership_type",
            field=models.CharField(choices=[("INEI", "INEI"), ("PROVIDER", "Provider")], default="INEI", max_length=20),
        ),
        migrations.AddConstraint(
            model_name="asset",
            constraint=models.UniqueConstraint(
                condition=Q(station_code__isnull=False),
                fields=("location", "station_code"),
                name="asset_unique_station_per_location",
            ),
        ),
    ]
