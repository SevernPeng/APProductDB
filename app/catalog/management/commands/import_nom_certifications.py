from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import Product, normalize_model_key
from catalog.nom import has_current_nom, matches_product, read_tracker


class Command(BaseCommand):
    help = "Import TP-Link NOM tracker evidence from .xls (replace this tracker snapshot)."

    def add_arguments(self, parser):
        parser.add_argument("path", type=Path)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            records = read_tracker(options["path"])
        except (OSError, ValueError, KeyError) as exc:
            raise CommandError(str(exc)) from exc
        by_model = defaultdict(list)
        for record in records:
            by_model[record["model_key"]].append(record)
        matched = certified = 0
        changed = []
        for product in Product.objects.select_related("brand").all():
            if normalize_model_key(product.brand.name) != "TPLINK":
                continue
            evidence = [r for r in by_model[product.model_key] if matches_product(r, product)]
            matched += bool(evidence)
            certified += has_current_nom(evidence)
            if product.nom_records != evidence:
                product.nom_records = evidence
                changed.append(product)
        if not options["dry_run"]:
            with transaction.atomic():
                Product.objects.bulk_update(changed, ["nom_records"])
        prefix = "DRY RUN: " if options["dry_run"] else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}{len(records)} tracker rows; {matched} products matched; "
            f"{certified} with NOM; {len(changed)} products updated."
        ))
