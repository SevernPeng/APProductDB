from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


ROUTER_URL = "https://www.trendnet.com/products/business-router/gigabit-multi-wan-vpn-business-router-TWG-431BR"
BRIDGE_URL = "https://downloads.trendnet.com/tew-840apbo/datasheet/en_datasheet_tew-840apbo_%28v1.0r%29.pdf"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


PRODUCTS = {
    "TWG-431BR": {
        "url": ROUTER_URL,
        "title": "TRENDnet TWG-431BR official product page",
        "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "location": "Specifications section",
        "values": {
            "concurrent_sessions": n(50000, "Maximum Concurrent Sessions: 50,000"),
            "controller_management": t("HTTP/HTTPS web UI; CLI via console, Telnet, or SSHv2; SNMP v1/v2c/v3; syslog"),
            "dimensions_mm": t("265 x 185 x 44.45 mm"),
            "firewall_features": t("SPI firewall; NAT/SNAT/PAT; MAC, IP, URL, keyword, P2P and IM filtering; DMZ; VPN passthrough"),
            "lan_interfaces": t("1 to 4 configurable Gigabit Ethernet LAN ports"),
            "max_power_consumption_w": n(17.4),
            "nat_throughput_mbps": n(900),
            "operating_temperature_c": t("0 to 50 °C"),
            "routing_throughput_mbps": n(900),
            "sd_wan": t("Multi-WAN load balancing and failover; no SD-WAN feature is advertised"),
            "uplink_interfaces": t("5 configurable Gigabit Ethernet ports; up to 4 may operate as WAN uplinks"),
            "usb_interfaces": t("1 x USB 3.0 for configuration backup/restore and log export"),
            "vpn_protocols": t("IPsec, SSL, PPTP, L2TP, and L2TP over IPsec"),
            "vpn_throughput_mbps": n(200, "IPsec AES-256/SHA-256 LAN-to-LAN throughput: 200 Mbps; SSL VPN: 20 Mbps"),
            "vpn_tunnels": n(30, "Up to 30 SSL VPN client-to-site tunnels; 5 IPsec tunnels; 15 PPTP/L2TP tunnels"),
            "wan_interfaces": t("1 to 4 configurable Gigabit Ethernet WAN ports"),
            "wan_load_balancing": b(True, "WAN load balancing by percentage/bandwidth, source IP, source/destination IP, or session"),
        },
    },
    "TEW-840APBO": {
        "url": BRIDGE_URL,
        "title": "TRENDnet TEW-840APBO v1.0R Data Sheet",
        "document_type": SourceDocument.DocumentType.DATASHEET,
        "location": "Technical specifications",
        "values": {
            "ethernet_interfaces": t("1 x Gigabit proprietary PoE-in LAN1; 1 x Gigabit LAN2"),
            "ip_rating": t("IP56"),
            "lightning_protection_kv": t("2 kV line-to-ground surge protection; 4 kV contact / 8 kV air ESD"),
            "max_power_consumption_w": n(9.5),
            "poe_input": t("24 V DC, 0.6 A proprietary/passive PoE injector; maximum PoE cable length 60 m"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified TRENDnet gateway and wireless bridge specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="TRENDnet").first()
        if not brand:
            raise CommandError("Missing brand: TRENDnet")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        for item in PRODUCTS.values():
            documents[item["url"]], _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Official source; accessed 2026-10-15",
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": item["document_type"],
                    "title": item["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing TRENDnet product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or
                    existing.value_boolean is not None
                ))
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else (
                        existing.value_number if existing.value_number is not None else existing.value_boolean
                    )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": f"Manually verified from {item['title']}, {item['location']}.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value)); new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value); new_value = bool(value)
                else:
                    defaults["value_text"] = str(value); new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    newly_filled += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[item["url"]],
                    source_location=f"{item['location']} - {model} - {code}",
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
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
