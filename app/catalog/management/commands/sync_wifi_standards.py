import json

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalog.models import Product
from catalog.wifi_standards import standard_assignments


class Command(BaseCommand):
    help = "Apply Omada EAP naming and competitor benchmark Wi-Fi generation rules."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        assignments, conflicts = standard_assignments()
        changed = []
        for product in Product.objects.filter(pk__in=assignments):
            standard = assignments[product.pk]
            if product.wifi_standard != standard:
                changed.append({"id": product.pk, "model": product.model,
                                "before": product.wifi_standard, "after": standard})
                Product.objects.filter(pk=product.pk).update(wifi_standard=standard, updated_at=timezone.now())
        if options["dry_run"]:
            transaction.set_rollback(True)
        self.stdout.write(json.dumps({"dry_run": options["dry_run"], "matched": len(assignments),
                                     "changed": changed, "conflicts": conflicts}))
