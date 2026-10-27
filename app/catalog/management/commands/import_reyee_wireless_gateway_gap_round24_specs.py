from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-EG105GW-X": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/wireless-router/eg105gwx/",
        "values": {
            "concurrent_sessions": (160, "Recommended number of concurrent clients: 160"),
            "controller_management": ("Ruijie Cloud; Ruijie Reyee App", "Free cloud management; mobile-app network construction"),
            "dimensions_mm": ("283 x 172 x 46 mm", "Product dimensions (W x D x H): 283 mm x 172 mm x 46 mm, excluding antennas and foot pads"),
            "ethernet_interfaces": ("5 x 10/100/1000BASE-T RJ45", "Number of 10/100/1000BASE-T ports: 5"),
            "lan_interfaces": ("1 fixed LAN port", "Number of fixed LAN ports: 1"),
            "max_channel_width_mhz": (160, "The product page describes use of the 160 MHz band"),
            "mesh_support": (True, "One-Click Reyee Mesh"),
            "router_supported_bands": ("2.4 GHz and 5 GHz", "Dual-band Wi-Fi 6 AX3000 wireless router"),
            "router_wifi_standard": ("Wi-Fi 6 (IEEE 802.11ax)", "Wi-Fi 6 (IEEE 802.11ax), compatible with IEEE 802.11a/b/g/n/ac"),
            "router_wireless_rate_mbps": (2974, "Maximum wireless data rate: 2974 Mbps"),
            "routing_throughput_mbps": (1200, "Throughput: 1200 Mbps"),
            "vpn_protocols": ("IPsec; OpenVPN; L2TP; PPTP", "IPSec, OpenVPN, L2TP, PPTP, etc."),
            "wan_interfaces": ("1 fixed WAN port; up to 4 WAN ports", "Number of fixed WAN ports: 1; load balancing on four WAN ports"),
            "wan_load_balancing": (True, "Load balancing on four WAN ports"),
        },
        "clear": {"cellular_standard", "cellular_downlink_mbps", "sim_interfaces"},
    },
    "RG-EG105GW(T)": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/wireless-router/rg-eg105gwt/",
        "values": {
            "concurrent_sessions": (150, "Recommended number of concurrent clients: 150"),
            "controller_management": ("Ruijie Cloud; Ruijie Reyee App", "Free cloud management; mobile-app network construction"),
            "dimensions_mm": ("120 x 28 x 120 mm", "Product dimensions (W x D x H): 120 mm x 28 mm x 120 mm, excluding mounting bracket"),
            "ethernet_interfaces": ("5 x 10/100/1000BASE-T RJ45", "Number of 10/100/1000BASE-T ports: 5"),
            "lan_interfaces": ("1 fixed LAN port", "Number of fixed LAN ports: 1"),
            "mesh_support": (True, "Reyee Mesh technology"),
            "router_supported_bands": ("2.4 GHz and 5 GHz", "Dual-band Wi-Fi 5 AC1266 wireless router"),
            "router_wifi_standard": ("Wi-Fi 5 (IEEE 802.11ac)", "Wi-Fi 5 (IEEE 802.11ac), compatible with IEEE 802.11a/b/g/n"),
            "router_wireless_rate_mbps": (1266, "Maximum wireless data rate: 1266 Mbps"),
            "routing_throughput_mbps": (700, "Throughput: 700 Mbps"),
            "vpn_protocols": ("IPsec; OpenVPN; L2TP; PPTP", "IPSec, OpenVPN, L2TP, PPTP, etc."),
            "wan_interfaces": ("1 fixed WAN port; up to 4 WAN ports", "Number of fixed WAN ports: 1; load balancing on four WAN ports"),
            "wan_load_balancing": (True, "Load balancing on four WAN ports"),
        },
        "clear": {"cellular_standard", "cellular_downlink_mbps", "sim_interfaces", "max_channel_width_mhz"},
    },
}


def comparable(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    if spec.value_boolean is not None:
        return spec.value_boolean
    if spec.value_number is not None:
        return spec.value_number
    if (spec.value_text or "").strip():
        return spec.value_text
    return None


class Command(BaseCommand):
    help = "Import manually verified Reyee wireless-gateway specifications (round 24)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        codes = {
            code
            for row in PRODUCTS.values()
            for code in set(row["values"]) | set(row["clear"])
        }
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = cleared = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version="Current official global product page, accessed 2026-10-21",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"{model} official product page",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = model_cleared = 0
            for code in row["clear"]:
                definition = definitions[code]
                spec = ProductSpec.objects.filter(product=product, definition=definition).first()
                if comparable(spec) is None:
                    continue
                SpecEvidence.objects.filter(product_spec=spec).delete()
                spec.value_status = ProductSpec.ValueStatus.UNKNOWN
                spec.value_text = ""
                spec.value_number = None
                spec.value_boolean = None
                spec.normalized_value = ""
                spec.raw_value = ""
                spec.source_url = ""
                spec.source_note = "Cleared because the official product page identifies a non-cellular wireless router and does not publish this value."
                spec.verified_date = accessed
                spec.save()
                cleared += 1
                model_cleared += 1

            for code, (value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = comparable(old)
                if isinstance(value, bool):
                    new_value = value
                elif isinstance(value, (int, float)):
                    new_value = Decimal(str(value))
                else:
                    new_value = str(value)
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": str(value) if isinstance(value, str) else "",
                    "value_number": new_value if isinstance(new_value, Decimal) else None,
                    "value_boolean": value if isinstance(value, bool) else None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": row["url"][:200],
                    "source_note": "Manually verified from the current official Reyee product page.",
                    "verified_date": accessed,
                }
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if old_value is None:
                    new += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Features / Key Specifications - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            details.append(
                f"{model}:+{model_new}/corrected:{model_corrected}/cleared:{model_cleared}"
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
                f"unchanged={unchanged} cleared={cleared} models={len(PRODUCTS)}"
            )
        )
        self.stdout.write("; ".join(details))
