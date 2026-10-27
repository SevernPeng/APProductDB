from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


DIS_100 = "https://www.dlink.com/en/-/media/business_products/dis/100g-8sw/datasheet/dis100ga1datasheetv200ww.pdf"
DIS_210 = "https://www.dlink.com/si/sl/-/media/product-pages/dis/210g-series/dis210gseriesa1datasheetv101ww.pdf"


UNMANAGED_COMMON = {
    "acl_security": t("Not supported (unmanaged switch)"),
    "fan_design": t("Fanless passive cooling"),
    "jumbo_frame_bytes": n(9216, "9 KB jumbo frame"),
    "l2_features": t("IEEE 802.3x flow control, broadcast/multicast/unicast storm control, IEEE 802.1p QoS, IEEE 802.3az EEE"),
    "mac_address_table": t("2K entries"),
    "operating_temperature_c": t("-40 to 75 °C"),
    "packet_forwarding_rate_mpps": n(7.44),
    "stp_features": t("Not supported (unmanaged switch)"),
    "switching_capacity_gbps": n(10),
    "transmission_method": t("Store-and-forward"),
}


MANAGED_COMMON = {
    "acl_security": t(
        "Ingress ACL: up to 895 IPv4 and 384 IPv6 entries; 802.1X/RADIUS, SSHv2, TLS 1.2, "
        "DHCP snooping, DAI, IP source guard, IMPB, BPDU attack protection"
    ),
    "fan_design": t("Fanless passive cooling"),
    "jumbo_frame_bytes": n(9216, "Jumbo frames up to 9K bytes"),
    "stp_features": t("IEEE 802.1D STP, IEEE 802.1w RSTP, IEEE 802.1s MSTP; BPDU filtering, root guard, loop guard"),
    "transmission_method": t("Store-and-forward"),
    "vlan_count": n(4094, "Maximum 4094 dynamic VLAN groups; configurable VID 1-4094"),
}


PRODUCTS = {
    "DIS-100G-5W": {
        "url": DIS_100,
        "title": "D-Link DIS-100G Series A1 Datasheet v2.00",
        "location": "DIS-100G-5W A1 column and shared specifications, pp. 1-3",
        "values": {
            **UNMANAGED_COMMON,
            "power_supply": t("Dual redundant 12-58 V DC terminal-block inputs; reverse-polarity protection"),
        },
    },
    "DIS-100G-5PSW": {
        "url": DIS_100,
        "title": "D-Link DIS-100G Series A1 Datasheet v2.00",
        "location": "DIS-100G-5PSW A1 column and shared specifications, pp. 1-3",
        "values": {
            **UNMANAGED_COMMON,
            "power_supply": t("Dual redundant 48-58 V DC terminal-block inputs; reverse-polarity protection"),
        },
    },
    "DIS-100G-8SW": {
        "url": DIS_100,
        "title": "D-Link DIS-100G Series A1 Datasheet v2.00",
        "location": "DIS-100G-8SW A1 column and shared specifications, pp. 1-3",
        "values": {
            "acl_security": t("Not supported (unmanaged switch)"),
            "fan_design": t("Fanless passive cooling"),
            "jumbo_frame_bytes": n(9216, "9 KB jumbo frame"),
            "l2_features": t("IEEE 802.3x flow control, broadcast/multicast/unicast storm control, IEEE 802.1p QoS, IEEE 802.3az EEE"),
            "mac_address_table": t("8K entries"),
            "packet_forwarding_rate_mpps": n(11.9),
            "power_supply": t("Dual redundant 12-58 V DC terminal-block inputs"),
            "stp_features": t("Not supported (unmanaged switch)"),
            "transmission_method": t("Store-and-forward"),
        },
    },
    "DIS-210G-06": {
        "url": DIS_210,
        "title": "D-Link DIS-210G Series A1 Datasheet v1.01",
        "location": "DIS-210G-06 A1 column and shared software specifications, pp. 3-7",
        "values": {
            **MANAGED_COMMON,
            "power_supply": t("Dual redundant 12-55 V DC terminal-block inputs"),
        },
    },
    "DIS-210G-06P": {
        "url": DIS_210,
        "title": "D-Link DIS-210G Series A1 Datasheet v1.01",
        "location": "DIS-210G-06P A1 column and shared software specifications, pp. 3-7",
        "values": {
            **MANAGED_COMMON,
            "power_supply": t("Dual redundant 48-55 V DC terminal-block inputs"),
            "poe_configuration": t("4 PoE+ ports; IEEE 802.3af/at; 30 W per port; 120 W total budget"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link DIS-100G and DIS-210G industrial-switch specifications (round 9)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        sources = {}
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published D-Link product: {model}")
            if row["url"] not in sources:
                sources[row["url"]], _ = SourceDocument.objects.update_or_create(
                    url=row["url"],
                    document_version="Exact A1 series datasheet accessed 2026-10-14",
                    defaults={
                        "brand": brand,
                        "product": None,
                        "document_type": SourceDocument.DocumentType.DATASHEET,
                        "title": row["title"],
                        "region": "Worldwide/official regional site",
                        "published_date": None,
                        "accessed_date": accessed,
                        "active": True,
                    },
                )
            source = sources[row["url"]]
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None
                ))
                if not had:
                    old_value = None
                elif old.value_text:
                    old_value = old.value_text
                elif old.value_number is not None:
                    old_value = old.value_number
                else:
                    old_value = old.value_boolean
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": row["url"][:200],
                    "source_note": "Manually verified from the exact A1 model column and shared feature table.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had:
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
                    source_location=f"{row['location']} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            details.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
