from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0006_registered_at_not_null"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="asset",
            name="asset_unique_station_per_location",
        ),
    ]
