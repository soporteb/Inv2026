from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="assetassignment",
            constraint=models.UniqueConstraint(
                fields=("asset",),
                condition=Q(is_current=True),
                name="unique_current_assignment_per_asset",
            ),
        ),
        migrations.AlterField(
            model_name="assetevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("CREATED", "Created"),
                    ("ASSIGNED", "Assigned"),
                    ("UPDATED", "Updated"),
                    ("REASSIGNED", "Reassigned"),
                ],
                max_length=30,
            ),
        ),
    ]
