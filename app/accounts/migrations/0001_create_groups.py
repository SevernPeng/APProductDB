from django.db import migrations


GROUP_NAMES = ("Viewer", "Contributor")


def create_groups(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    for name in GROUP_NAMES:
        group_model.objects.get_or_create(name=name)


def delete_groups(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    group_model.objects.filter(name__in=GROUP_NAMES).delete()


class Migration(migrations.Migration):
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [migrations.RunPython(create_groups, delete_groups)]
