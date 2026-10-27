from django.db import migrations


def clear_retired_file_references(apps, schema_editor):
    source_document = apps.get_model("catalog", "SourceDocument")
    source_document.objects.filter(file__startswith="datasheets/").update(file="")


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0008_remove_product_datasheet_url_and_more"),
    ]

    operations = [
        migrations.RunPython(
            clear_retired_file_references,
            migrations.RunPython.noop,
        ),
    ]
