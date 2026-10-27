from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


FIREWALL = (
    "ACL and IPv6 ACL; malformed-packet, fragmentation, Teardrop, LAND, SYN-flood, Smurf, "
    "and IP-attack defense; ping disable; stateful firewall/ACL; IP-MAC binding; "
    "network-sharing prevention; security log and zone; user-group connection limiting"
)


PRODUCTS = {
    "RG-EG105GW": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/wireless-router/rg-eg105gwt/",
        "title": "RG-EG105GW Family Official Product Page",
        "version": "Current official wireless-router family page, accessed 2026-10-21",
        "values": {},
        "clear": {
            "cellular_standard": "RG-EG105GW is a Wi-Fi router without an integrated cellular modem."
        },
    },
    "RG-EG105GW(T)": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/wireless-router/rg-eg105gwt/",
        "title": "RG-EG105GW(T) Official Product Page and Datasheet",
        "version": "Exact-model official datasheet 2026-03-02; current official product page",
        "values": {
            "max_power_consumption_w": n(15, "Maximum power consumption: 15 W"),
            "concurrent_sessions": n(12000, "Maximum number of concurrent sessions: 12000"),
            "vpn_throughput_mbps": n(24, "IPsec VPN bandwidth: 24 Mbps"),
            "vpn_tunnels": n(8, "Maximum number of branches in IPsec VPN networking: 8"),
            "sd_wan": t("80 Mbps; 24 tunnels; maximum 8 branches"),
            "firewall_features": t(FIREWALL),
            "max_channel_width_mhz": n(80, "Maximum 5 GHz channel width: 80 MHz"),
            "lightning_protection_kv": t(
                "Service port: +/-2 kV common mode; power connector: +/-4 kV common mode and +/-2 kV differential mode"
            ),
        },
        "clear": {},
    },
    "RG-EG105GW-X": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-router/wireless-router/eg105gwx/",
        "title": "RG-EG105GW-X Official Product Page and Datasheet",
        "version": "Exact-model datasheet 2025-10-15; current official product page",
        "values": {
            "max_power_consumption_w": n(20, "Maximum power consumption: 20 W"),
            "concurrent_sessions": n(30000, "Maximum number of concurrent sessions: 30000"),
            "vpn_throughput_mbps": n(100, "IPsec VPN bandwidth: 100 Mbps"),
            "vpn_tunnels": n(32, "Maximum number of branches in IPsec VPN networking: 32"),
            "sd_wan": t("300 Mbps; 96 tunnels; maximum 32 branches"),
            "firewall_features": t(FIREWALL),
            "lightning_protection_kv": t(
                "Service port: +/-2 kV common mode; power connector: +/-4 kV common mode and +/-2 kV differential mode"
            ),
        },
        "clear": {},
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
    help = "Import manually verified Reyee wireless-gateway specs (round 35)."

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
                url=row["url"], document_version=row["version"],
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": row["title"], "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )
            model_new = model_corrected = model_cleared = 0
            for code, note in row["clear"].items():
                spec = ProductSpec.objects.filter(product=product, definition=definitions[code]).first()
                if actual(spec) is None:
                    continue
                spec.evidence.all().delete()
                spec.value_status = ProductSpec.ValueStatus.UNKNOWN
                spec.value_text = ""; spec.value_number = None; spec.value_boolean = None
                spec.normalized_value = ""; spec.raw_value = ""; spec.source_url = ""
                spec.source_note = f"Manual source audit: {note}"
                spec.verified_date = accessed
                spec.save()
                cleared += 1; model_cleared += 1

            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = actual(old)
                new_value = Decimal(str(value)) if kind == "number" else str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": "" if kind == "number" else str(value),
                        "value_number": new_value if kind == "number" else None,
                        "value_boolean": None, "normalized_value": str(value), "unit": definition.unit,
                        "raw_value": raw, "source_url": row["url"][:200],
                        "source_note": "Manually verified from the newest available official exact-model product page and datasheet.",
                        "verified_date": accessed,
                    },
                )
                if old_value is None:
                    new += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location="Hardware, radio, security, SD-WAN, and VPN specification tables",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            details.append(f"{model}:+{model_new}/corrected:{model_corrected}/cleared:{model_cleared}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} cleared={cleared} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
