from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("changes", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="changerequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("approved", "Applied"),
                    ("rejected", "Rejected"),
                ],
                db_index=True,
                default="pending",
                max_length=20,
            ),
        ),
    ]
