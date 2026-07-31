from django.core.management.base import BaseCommand

from catalog.datasheets import process_datasheet_ingestion
from catalog.models import DatasheetIngestion, Product


class Command(BaseCommand):
    help = "Process pending Datasheet jobs or enqueue existing product Datasheet URLs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all-existing",
            action="store_true",
            help="Create a URL ingestion for every product with a Datasheet URL.",
        )
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        if options["all_existing"]:
            products = Product.objects.exclude(datasheet_url="").order_by("pk")[
                : options["limit"]
            ]
            for product in products:
                DatasheetIngestion.objects.create(
                    product=product,
                    source_type=DatasheetIngestion.SourceType.URL,
                    source_url=product.datasheet_url,
                )
        jobs = DatasheetIngestion.objects.filter(
            status=DatasheetIngestion.Status.PENDING
        ).order_by("created_at", "pk")[: options["limit"]]
        counts = {}
        for job in jobs:
            result = process_datasheet_ingestion(job.pk)
            counts[result.status] = counts.get(result.status, 0) + 1
            self.stdout.write(
                f"{result.product}: {result.get_status_display()} - "
                f"{result.validation_message}"
            )
        self.stdout.write(self.style.SUCCESS(f"Processed {sum(counts.values())}: {counts}"))
