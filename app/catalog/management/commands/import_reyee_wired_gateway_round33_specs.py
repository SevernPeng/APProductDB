from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value=True, raw=None):
    return "boolean", value, raw or ("Yes" if value else "No")


FIREWALL = (
    "ACL; malformed-packet, fragmentation, Teardrop, LAND, SYN-flood, Smurf, and IP-attack "
    "defense; ping disable; stateful firewall/ACL; IP-MAC binding; network-sharing prevention; "
    "security log and zone; user-group connection limiting"
)


PRODUCTS = {
    "RG-EG105G": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/eg-series/rg-eg105g-v2/",
        "title": "RG-EG105G V2 Official Product Page",
        "version": "Current official wired-router product page, accessed 2026-10-21",
        "location": "Product identity and hardware specification tables",
        "values": {},
        "clear": {
            "cellular_standard": "RG-EG105G is a wired Ethernet gateway and has no cellular modem.",
            "router_supported_bands": "RG-EG105G is a wired gateway and has no Wi-Fi radio bands.",
            "router_wifi_standard": "RG-EG105G is a wired gateway and has no Wi-Fi radio standard.",
        },
    },
    "RG-EG1510XS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/eg-series/eg1510xs/",
        "title": "RG-EG1510XS Official Product Page and Datasheet",
        "version": "Exact-model datasheet 2025-12-04; current official product page",
        "location": "Hardware and software specification tables",
        "values": {
            "max_power_consumption_w": n(20, "Maximum power consumption: 20 W"),
            "concurrent_sessions": n(300000, "Maximum number of concurrent sessions: 300000"),
            "vpn_throughput_mbps": n(1100, "IPsec VPN bandwidth: 1100 Mbps"),
            "wan_load_balancing": b(True, "Multi-WAN intelligent load balancing: supported"),
            "sd_wan": t("1200 Mbps; 3000 tunnels; maximum 1000 branches"),
            "firewall_features": t(FIREWALL),
            "lightning_protection_kv": t(
                "Service port: +/-6 kV common mode; power connector: +/-6 kV common and differential mode"
            ),
        },
        "clear": {
            "cellular_standard": "RG-EG1510XS is a wired gateway and has no cellular modem.",
            "router_supported_bands": "RG-EG1510XS is a wired gateway and has no Wi-Fi radio bands.",
            "router_wifi_standard": "RG-EG1510XS is a wired gateway and has no Wi-Fi radio standard.",
        },
    },
    "RG-EG209GS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/eg-series/rg-eg209gs/",
        "title": "RG-EG209GS Official Product Page and Datasheet",
        "version": "Exact-model datasheet 2026-08-07; current official product page",
        "location": "Hardware and software specification tables",
        "values": {
            "max_power_consumption_w": n(18, "Maximum power consumption: 18 W"),
            "concurrent_sessions": n(60000, "Maximum number of concurrent sessions: 60000"),
            "vpn_throughput_mbps": n(28, "IPsec VPN bandwidth: 28 Mbps"),
            "wan_load_balancing": b(True, "Intelligent load balancing; maximum 4 WAN ports"),
            "sd_wan": t("80 Mbps; 24 tunnels; maximum 8 branches"),
            "firewall_features": t(FIREWALL),
            "lightning_protection_kv": t(
                "Service port: +/-4 kV common mode; power connector: +/-4 kV common and differential mode"
            ),
        },
        "clear": {
            "cellular_standard": "RG-EG209GS is a wired gateway and has no cellular modem.",
            "router_supported_bands": "RG-EG209GS is a wired gateway and has no Wi-Fi radio bands.",
            "router_wifi_standard": "RG-EG209GS is a wired gateway and has no Wi-Fi radio standard.",
        },
    },
    "RG-EG406XS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/eg-series/rg-eg406xs/",
        "title": "RG-EG406XS Official Product Page and Datasheet",
        "version": "Exact-model datasheet 2025-11-21; current official product page",
        "location": "Hardware and software specification tables",
        "values": {
            "max_power_consumption_w": n(9, "Maximum power consumption: 9 W"),
            "concurrent_sessions": n(120000, "Maximum number of concurrent sessions: 120000"),
            "vpn_throughput_mbps": n(700, "IPsec VPN bandwidth: 700 Mbps"),
            "wan_load_balancing": b(True, "Multi-WAN smart load balancing; maximum 5 WAN ports"),
            "sd_wan": t("750 Mbps; 300 tunnels; maximum 100 branches"),
            "firewall_features": t(FIREWALL),
            "lightning_protection_kv": t(
                "Service port: +/-4 kV common mode; power connector: +/-4 kV common and differential mode"
            ),
        },
        "clear": {
            "cellular_standard": "RG-EG406XS is a wired gateway and has no cellular modem.",
            "router_supported_bands": "RG-EG406XS is a wired gateway and has no Wi-Fi radio bands.",
            "router_wifi_standard": "RG-EG406XS is a wired gateway and has no Wi-Fi radio standard.",
        },
    },
    "RG-EG710XS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/eg-series/rg-eg710xs/",
        "title": "RG-EG710XS Official Product Page and Datasheet",
        "version": "Exact-model datasheet 2025-10-11; current official product page",
        "location": "Hardware and software specification tables",
        "values": {
            "max_power_consumption_w": n(14, "Maximum power consumption: 14 W"),
            "concurrent_sessions": n(150000, "Maximum number of concurrent sessions: 150000"),
            "vpn_throughput_mbps": n(1100, "IPsec VPN bandwidth: 1100 Mbps"),
            "wan_load_balancing": b(True, "Multi-WAN intelligent load balancing; maximum 9 WAN ports"),
            "sd_wan": t("1100 Mbps; 1500 tunnels; maximum 300 branches"),
            "firewall_features": t(FIREWALL),
            "lightning_protection_kv": t(
                "Service port: +/-6 kV common mode; power connector: +/-6 kV common and differential mode"
            ),
        },
        "clear": {
            "cellular_standard": "RG-EG710XS is a wired gateway and has no cellular modem.",
            "router_supported_bands": "RG-EG710XS is a wired gateway and has no Wi-Fi radio bands.",
            "router_wifi_standard": "RG-EG710XS is a wired gateway and has no Wi-Fi radio standard.",
        },
    },
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    if spec.value_number is not None:
        return spec.value_number
    if spec.value_boolean is not None:
        return spec.value_boolean
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import manually verified Reyee wired-gateway specs and clear invalid radio fields (round 33)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        codes = {code for row in PRODUCTS.values() for code in set(row["values"]) | set(row["clear"])}
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
                document_version=row["version"],
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": row["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = model_cleared = 0
            for code, note in row["clear"].items():
                spec = ProductSpec.objects.filter(product=product, definition=definitions[code]).first()
                if actual(spec) is None:
                    continue
                spec.evidence.all().delete()
                spec.value_status = ProductSpec.ValueStatus.UNKNOWN
                spec.value_text = ""
                spec.value_number = None
                spec.value_boolean = None
                spec.normalized_value = ""
                spec.raw_value = ""
                spec.source_url = ""
                spec.source_note = f"Manual source audit: {note}"
                spec.verified_date = accessed
                spec.save()
                cleared += 1
                model_cleared += 1

            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = actual(old)
                if kind == "number":
                    new_value = Decimal(str(value))
                elif kind == "boolean":
                    new_value = bool(value)
                else:
                    new_value = str(value)
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": str(value) if kind == "text" else "",
                    "value_number": new_value if kind == "number" else None,
                    "value_boolean": new_value if kind == "boolean" else None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": row["url"][:200],
                    "source_note": "Manually verified from the newest available official exact-model product page and datasheet.",
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
                    source_location=row["location"],
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
