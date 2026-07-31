from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Product
from catalog.services import backfill_product_spec_placeholders


class Command(BaseCommand):
    help = "Create Unknown ProductSpec rows for every active field applicable to each product."

    def add_arguments(self, parser):
        parser.add_argument("--published-only", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        products = Product.objects.select_related("category")
        if options["published_only"]:
            products = products.filter(is_published=True)
        created = backfill_product_spec_placeholders(products)
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "BACKFILLED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: products={products.count()} placeholders_created={created}"
            )
        )
