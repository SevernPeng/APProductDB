from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from catalog.datasheets import schedule_url_ingestion
from catalog.models import Product


@receiver(pre_save, sender=Product)
def remember_datasheet_url_change(sender, instance, **kwargs):
    if not instance.pk:
        instance._datasheet_url_changed = bool(instance.datasheet_url)
        return
    previous = sender.objects.filter(pk=instance.pk).values_list(
        "datasheet_url",
        flat=True,
    ).first()
    instance._datasheet_url_changed = previous != instance.datasheet_url


@receiver(post_save, sender=Product)
def enqueue_datasheet_url(sender, instance, **kwargs):
    if (
        settings.DATASHEET_AUTO_INGEST
        and getattr(instance, "_datasheet_url_changed", False)
        and instance.datasheet_url
    ):
        transaction.on_commit(
            lambda: schedule_url_ingestion(
                instance.pk,
                requested_by_id=instance.updated_by_id,
            )
        )
