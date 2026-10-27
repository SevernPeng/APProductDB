from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


CRS_L2 = "802.1Q bridge VLAN filtering; STP/RSTP/MSTP; LACP; IGMP snooping; port mirroring; QoS"
CRS_MGMT = "RouterOS via WinBox, WebFig, SSH, CLI and API; SwitchOS web interface; serial console"
CRS_ACL = "RouterOS bridge firewall/filtering and switch-chip ACL rules; management service access control"

PRODUCTS = {
    "CRS309-1G-8S+IN": {
        "url": "https://mikrotik.com/product/crs309_1g_8s_in",
        "values": {
            "ethernet_interfaces": t("1 x 1GbE RJ45 management/PoE-in; 8 x 10GbE SFP+"),
            "uplink_interfaces": t("8 x 10GbE SFP+"),
            "switching_capacity_gbps": n(162, "Non-blocking Layer 1 capacity: 162,000 Mbps"),
            "packet_forwarding_rate_mpps": n(120.536, "64-byte non-blocking switching: 120,535.7 kpps"),
            "fan_design": t("Passive cooling; fanless"),
            "power_supply": t("12-57 V DC jack or IEEE 802.3af/at PoE-in"),
            "operating_temperature_c": t("-40 to 70 °C"),
            "management_methods": t(CRS_MGMT), "l2_features": t(CRS_L2),
            "stp_features": t("STP, RSTP and MSTP; hardware offload"), "acl_security": t(CRS_ACL),
        },
    },
    "CRS317-1G-16S+RM": {
        "url": "https://mikrotik.com/product/crs317_1g_16s_rm",
        "values": {
            "ethernet_interfaces": t("1 x 1GbE RJ45 management; 16 x 10GbE SFP+"),
            "uplink_interfaces": t("16 x 10GbE SFP+"),
            "switching_capacity_gbps": n(322, "Non-blocking Layer 1 capacity: 322,000 Mbps"),
            "packet_forwarding_rate_mpps": n(239.583, "64-byte non-blocking switching: 239,583.3 kpps"),
            "fan_design": t("Passive cooling under normal conditions; 2 redundant emergency fans"),
            "power_supply": t("2 x redundant internal 100-240 V AC power supplies"),
            "operating_temperature_c": t("-20 to 60 °C"),
            "management_methods": t(CRS_MGMT), "l2_features": t(CRS_L2),
            "stp_features": t("STP, RSTP and MSTP; hardware offload"), "acl_security": t(CRS_ACL),
        },
    },
    "CRS326-24S+2Q+RM": {
        "url": "https://mikrotik.com/product/crs326_24s_2q_rm",
        "values": {
            "ethernet_interfaces": t("24 x 10GbE SFP+; 2 x 40GbE QSFP+; 1 x 10/100 RJ45 management"),
            "uplink_interfaces": t("24 x 10GbE SFP+; 2 x 40GbE QSFP+"),
            "switching_capacity_gbps": n(640, "Published switching capacity: 640 Gbps"),
            "packet_forwarding_rate_mpps": n(476.339, "64-byte non-blocking switching: 476,339.3 kpps"),
            "fan_design": t("3 internal fans"),
            "power_supply": t("2 x redundant internal 100-240 V AC power supplies"),
            "operating_temperature_c": t("-20 to 60 °C"),
            "management_methods": t(CRS_MGMT), "l2_features": t(CRS_L2),
            "stp_features": t("STP, RSTP and MSTP; hardware offload"), "acl_security": t(CRS_ACL),
        },
    },
    "CRS328-4C-20S-4S+RM": {
        "url": "https://mikrotik.com/product/crs328_4c_20s_4s_rm",
        "values": {
            "ethernet_interfaces": t("20 x 1GbE SFP; 4 x 10GbE SFP+; 4 x combo 1GbE RJ45/SFP"),
            "uplink_interfaces": t("20 x 1GbE SFP; 4 x 10GbE SFP+; 4 x combo 1GbE RJ45/SFP"),
            "switching_capacity_gbps": n(128, "Non-blocking Layer 1 capacity: 128,000 Mbps"),
            "packet_forwarding_rate_mpps": n(95.238, "64-byte non-blocking switching: 95,238.1 kpps"),
            "fan_design": t("2 internal fans"),
            "power_supply": t("2 x redundant internal 100-240 V AC power supplies"),
            "operating_temperature_c": t("-20 to 60 °C"),
            "management_methods": t(CRS_MGMT), "l2_features": t(CRS_L2),
            "stp_features": t("STP, RSTP and MSTP; hardware offload"), "acl_security": t(CRS_ACL),
        },
    },
    "RB260GSP": {
        "url": "https://mikrotik.com/product/RB260GSP",
        "values": {
            "ethernet_interfaces": t("5 x 1GbE RJ45; 1 x 1GbE SFP"),
            "uplink_interfaces": t("1 x 1GbE SFP"),
            "switching_capacity_gbps": n(12, "Non-blocking Layer 1 capacity: 12,000 Mbps"),
            "packet_forwarding_rate_mpps": n(8.929, "64-byte non-blocking switching: 8,928.6 kpps"),
            "fan_design": t("Passive cooling; fanless"),
            "power_supply": t("11-30 V DC jack or passive PoE-in; 24 V 2.5 A adapter included"),
            "operating_temperature_c": t("-20 to 70 °C"),
            "management_methods": t("SwitchOS web interface"),
            "l2_features": t("802.1Q VLAN; STP/RSTP; port isolation; link aggregation; port mirroring; bandwidth limiting"),
            "stp_features": t("STP and RSTP"),
            "acl_security": t("SwitchOS MAC-based forwarding/filtering and management access control"),
            "poe_ports": n(4, "Passive PoE-out on Ether2-Ether5"),
            "poe_standard": t("Passive PoE-out at the input voltage"),
            "max_poe_per_port_w": n(24, "1 A per-port limit at the included 24 V supply voltage"),
            "poe_budget_w": n(48, "2 A maximum total output at the included 24 V supply voltage"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified MikroTik switch specifications (round 1)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="MikroTik").first()
        if not brand:
            raise CommandError("Missing brand: MikroTik")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing MikroTik product: {model}")
            document, _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Current official product page and switching-test table; accessed 2026-10-15",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"MikroTik {model} product specifications and switching results",
                    "region": "Global", "published_date": None, "accessed_date": accessed, "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None
                ))
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else existing.value_number if existing.value_number is not None else existing.value_boolean
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": "Manually verified from MikroTik's current exact-model product page and official RouterOS/SwitchOS documentation.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value)); new_value = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value); new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had:
                    newly_filled += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=document,
                    source_location=f"Official specification/switching results - {model} - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
