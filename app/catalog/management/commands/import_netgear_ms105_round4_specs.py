from django.core.management.base import CommandError
from django.db import transaction

from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    b,
    n,
    t,
)
from catalog.models import Brand, Product, normalize_model_key


MS105_DS = "https://www.downloads.netgear.com/files/GDC/MS105/MS105_DS.pdf"


PRODUCTS = {
    "MS105": {
        "url": MS105_DS,
        "page": "pp. 1 and 3-4, highlights and technical specifications",
        "title": "NETGEAR MS105 5-Port Multi-Gigabit Ethernet Unmanaged Switch Data Sheet",
        "values": {
            "dimensions_mm": t(
                "158 x 101 x 29 mm (W x D x H)",
                "Dimensions (W x D x H): 158 x 101 x 29 mm",
            ),
            "fanless": b(True, "Fan/Fanless: Fanless; 0 dBA at 25 °C"),
            "installation": t(
                "Desktop or wall mount",
                "Form factor: Desktop/Wall mount; wall installation kit included",
            ),
            "max_power_consumption_w": n(
                9.24,
                "Power consumption: 9.24 W maximum; 4.60 W minimum/standby",
            ),
            "operating_temperature_c": t(
                "0 to 40 °C",
                "Operating temperature: 32 to 104 °F (0 to 40 °C)",
            ),
            "qos_support": t(
                "IEEE 802.1p QoS/CoS and DSCP tag honoring; WRR",
                "802.1p-based QoS/CoS: Yes; honors DSCP tags: Yes; queue WRR ratio 1:3:5:7:8:10:12:15",
            ),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Correct the NETGEAR MS105 model name and import current official physical and power specifications."
    products = PRODUCTS
    document_version = "MS105_DS_3Jan23; current official product page and data sheet accessed 2026-10-22"
    brand_name = "NETGEAR"

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name=self.brand_name).first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        product = Product.objects.filter(
            brand=brand,
            model__in=["MS105G", "MS105"],
            is_published=True,
        ).first()
        if not product:
            raise CommandError("Missing NETGEAR product: MS105G / MS105")

        renamed = product.model != "MS105"
        if renamed:
            corrected_key = normalize_model_key("MS105")
            if Product.objects.filter(
                brand=brand,
                model_key=corrected_key,
                region=product.region,
                hardware_version=product.hardware_version,
            ).exclude(pk=product.pk).exists():
                raise CommandError("Cannot rename MS105G: a matching MS105 product already exists")
            if product.product_model:
                canonical = product.product_model
                canonical.model = "MS105"
                canonical.product_name = "5-Port Multi-Gigabit (2.5G) Ethernet Unmanaged Switch"
                canonical.summary = "Five-port 2.5GbE unmanaged desktop or wall-mount switch."
                canonical.save(
                    update_fields=[
                        "model",
                        "model_key",
                        "product_name",
                        "summary",
                        "updated_at",
                    ]
                )
            product.model = "MS105"
            product.official_url = "https://www.netgear.com/business/wired/switches/unmanaged/ms105/"
            product.notes = (
                (product.notes or "")
                + "\nCorrected model from MS105G to the official NETGEAR MS105 nomenclature on 2026-10-22."
            ).strip()
            product.save(update_fields=["model", "model_key", "official_url", "notes", "updated_at"])

        super().handle(*args, **options)
        if options["dry_run"]:
            transaction.set_rollback(True)
        self.stdout.write(f"model_renamed={int(renamed)}")
