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


URLS = {
    "2136": "https://www.draytek.com/products/vigor2136/",
    "2927": "https://www.draytek.com/products/vigor2927/",
    "2962": "https://www.draytek.com/products/vigor2962/",
    "3912": "https://www.draytek.com/products/vigor3912/",
}

VPN_2927 = "PPTP; L2TP; IPsec; L2TP over IPsec; SSL; GRE; IKEv2; IKEv2-EAP; IPsec-XAuth; OpenVPN; WireGuard"
FIREWALL_2927 = (
    "NAT and ALG; VPN pass-through; IP-based firewall policy; application, URL, DNS and web-category "
    "content filtering; DoS and spoofing defense"
)
MGMT_2927 = (
    "Local HTTP/HTTPS/Telnet/SSH/FTP; TR-069; VigorACS 3; on-router management for up to "
    "20 VigorAPs and 10 VigorSwitches"
)


PRODUCTS = {
    "Vigor 2136": {
        "source": "2136",
        "values": {
            "ethernet_interfaces": t("1 x 2.5GbE WAN; 1 x 2.5GbE LAN/WAN; 3 x 1GbE LAN"),
            "wan_interfaces": t("1 x 2.5GbE fixed WAN + 1 x 2.5GbE switchable LAN/WAN"),
            "lan_interfaces": t("3 x 1GbE fixed LAN + 1 x 2.5GbE switchable LAN/WAN"),
            "concurrent_sessions": n(50000, "50k sessions"),
            "nat_throughput_mbps": n(2300, "Max. NAT: 2300 Mbps"),
            "vpn_throughput_mbps": n(390, "IPsec VPN throughput up to 390 Mbps"),
            "vpn_tunnels": n(16, "16 VPN tunnels"),
            "vpn_protocols": t("IPsec; L2TP over IPsec; IKEv1/IKEv2; IKEv2-EAP; IPsec-XAuth; OpenVPN; WireGuard"),
            "wan_load_balancing": b(True, "Dual-WAN load balancing and failover"),
            "firewall_features": t(
                "URL/IP reputation; threat protection; firewall filtering; port knocking; ARP/IP spoofing defense; "
                "MAC filtering; IPv6 address security"
            ),
            "controller_management": t(
                "Local HTTP/HTTPS/Telnet/SSH/FTP; TR-069; VigorACS 3; virtual controllers for up to "
                "20 VigorAPs and 5 VigorSwitches"
            ),
            "sd_wan": t("VigorACS 3 application-based SD-WAN policy"),
            "max_power_consumption_w": n(10, "Max. power consumption: 10 W"),
            "dimensions_mm": t("207 x 131 x 42 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
        },
    },
    "Vigor2927": {
        "source": "2927",
        "values": {
            "ethernet_interfaces": t("1 x 1GbE fixed WAN; 1 x 1GbE switchable LAN/WAN; 5 x 1GbE fixed LAN"),
            "wan_interfaces": t("1 x 1GbE fixed WAN + 1 x 1GbE switchable LAN/WAN"),
            "lan_interfaces": t("5 x 1GbE fixed LAN + 1 x 1GbE switchable LAN/WAN"),
            "concurrent_sessions": n(60000, "60k NAT sessions"),
            "nat_throughput_mbps": n(1800, "Max. NAT with hardware acceleration, dual WAN: 1800 Mbps"),
            "vpn_throughput_mbps": n(800, "IPsec VPN throughput with hardware NAT enabled: 800 Mbps"),
            "vpn_tunnels": n(50),
            "vpn_protocols": t(VPN_2927),
            "wan_load_balancing": b(True, "IP-based and session-based load balancing; failover"),
            "firewall_features": t(FIREWALL_2927),
            "controller_management": t(MGMT_2927),
            "sd_wan": t("VigorACS 3 application-based SD-WAN policy"),
            "max_power_consumption_w": n(21.6),
            "dimensions_mm": t("241 x 165 x 44 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
        },
    },
    "Vigor 2927F": {
        "source": "2927",
        "values": {
            "ethernet_interfaces": t("1 x 1GbE SFP WAN; 1 x 1GbE RJ45 switchable LAN/WAN; 5 x 1GbE fixed LAN"),
            "wan_interfaces": t("1 x 1GbE SFP WAN + 1 x 1GbE RJ45 switchable LAN/WAN"),
            "lan_interfaces": t("5 x 1GbE fixed LAN + 1 x 1GbE RJ45 switchable LAN/WAN"),
            "concurrent_sessions": n(60000, "60k NAT sessions"),
            "nat_throughput_mbps": n(1800, "Max. NAT with hardware acceleration, dual WAN: 1800 Mbps"),
            "vpn_throughput_mbps": n(800, "IPsec VPN throughput with hardware NAT enabled: 800 Mbps"),
            "vpn_tunnels": n(50),
            "vpn_protocols": t(VPN_2927),
            "wan_load_balancing": b(True, "IP-based and session-based load balancing; failover"),
            "firewall_features": t(FIREWALL_2927),
            "controller_management": t(MGMT_2927),
            "sd_wan": t("VigorACS 3 application-based SD-WAN policy"),
            "max_power_consumption_w": n(21.6),
            "dimensions_mm": t("241 x 165 x 44 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
        },
    },
    "Vigor2927ax": {
        "source": "2927",
        "values": {
            "ethernet_interfaces": t("1 x 1GbE fixed WAN; 1 x 1GbE switchable LAN/WAN; 5 x 1GbE fixed LAN"),
            "wan_interfaces": t("1 x 1GbE fixed WAN + 1 x 1GbE switchable LAN/WAN"),
            "lan_interfaces": t("5 x 1GbE fixed LAN + 1 x 1GbE switchable LAN/WAN"),
            "concurrent_sessions": n(60000, "60k NAT sessions"),
            "nat_throughput_mbps": n(1800, "Max. NAT with hardware acceleration, dual WAN: 1800 Mbps"),
            "vpn_throughput_mbps": n(800, "IPsec VPN throughput with hardware NAT enabled: 800 Mbps"),
            "vpn_tunnels": n(50),
            "vpn_protocols": t(VPN_2927),
            "wan_load_balancing": b(True, "IP-based and session-based load balancing; failover"),
            "firewall_features": t(FIREWALL_2927),
            "controller_management": t(MGMT_2927),
            "sd_wan": t("VigorACS 3 application-based SD-WAN policy"),
            "max_power_consumption_w": n(26.4),
            "dimensions_mm": t("241 x 165 x 44 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
        },
    },
    "Vigor2962": {
        "source": "2962",
        "values": {
            "ethernet_interfaces": t(
                "1 x 2.5GbE RJ45 WAN/LAN; 1 x 1GbE RJ45/SFP combo WAN/LAN; "
                "2 x 1GbE RJ45 WAN/LAN; 2 x 1GbE fixed LAN"
            ),
            "wan_interfaces": t(
                "Up to 4 switchable WANs: 1 x 2.5GbE RJ45, 1 x 1GbE RJ45/SFP combo, 2 x 1GbE RJ45"
            ),
            "lan_interfaces": t(
                "2 x 1GbE fixed LAN plus 1 x 2.5GbE, 1 x 1GbE RJ45/SFP combo and 2 x 1GbE switchable WAN/LAN"
            ),
            "concurrent_sessions": n(300000, "300k sessions"),
            "nat_throughput_mbps": n(2200, "Max. NAT throughput: 2.2 Gbps"),
            "vpn_throughput_mbps": n(1000, "IPsec VPN throughput up to 1 Gbps"),
            "vpn_tunnels": n(200),
            "vpn_protocols": t("PPTP; L2TP; IPsec; L2TP over IPsec; SSL; GRE; IKEv2; IKEv2-EAP; IPsec-XAuth; OpenVPN; WireGuard"),
            "wan_load_balancing": b(True, "Up to four WANs for load balancing/failover"),
            "firewall_features": t(
                "NAT and ALG; VPN pass-through; IP-based firewall policy; application, URL, DNS and web-category "
                "content filtering; DoS and spoofing defense"
            ),
            "controller_management": t(
                "Local HTTP/HTTPS/Telnet/SSH/FTP; TR-069; VigorACS 3; on-router management for up to "
                "50 VigorAPs and 30 VigorSwitches"
            ),
            "sd_wan": t("VigorACS 3 application-based SD-WAN policy"),
            "max_power_consumption_w": n(15),
            "dimensions_mm": t("273 x 171 x 45 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
        },
    },
    "Vigor 3912": {
        "source": "3912",
        "values": {
            "ethernet_interfaces": t(
                "2 x 10GbE SFP+ WAN/LAN; 2 x 2.5GbE RJ45 WAN/LAN; "
                "4 x 1GbE RJ45 WAN/LAN; 4 x 1GbE fixed LAN"
            ),
            "wan_interfaces": t("Up to 8 WANs: 2 x 10GbE SFP+, 2 x 2.5GbE RJ45 and 4 x 1GbE RJ45, all WAN/LAN switchable"),
            "lan_interfaces": t("4 x 1GbE fixed LAN plus 8 switchable WAN/LAN interfaces"),
            "concurrent_sessions": n(1000000, "1000k NAT sessions"),
            "nat_throughput_mbps": n(15600, "15.6 Gbps NAT throughput, bi-directional"),
            "vpn_throughput_mbps": n(5700, "5.7 Gbps IPsec VPN throughput, bi-directional"),
            "vpn_tunnels": n(500),
            "vpn_protocols": t("PPTP; L2TP; IPsec; L2TP over IPsec; SSL; GRE; IKEv2; IPsec-XAuth; OpenVPN; WireGuard"),
            "wan_load_balancing": b(True, "Multi-WAN load balancing and failover"),
            "firewall_features": t(
                "NAT, Fast NAT and server load balancing; ALG; VPN pass-through; IP-based firewall policy; "
                "application, URL, DNS and web-category filtering; DoS and spoofing defense"
            ),
            "controller_management": t(
                "Local HTTP/HTTPS/Telnet/SSH/FTP; TR-069; VigorACS 3; on-router management for up to "
                "50 VigorAPs and 30 VigorSwitches"
            ),
            "sd_wan": t("VigorACS 3 application-based SD-WAN policy"),
            "max_power_consumption_w": n(35),
            "dimensions_mm": t("443 x 285 x 45 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified DrayTek gateway specifications (round 1)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="DrayTek").first()
        if not brand:
            raise CommandError("Missing brand: DrayTek")

        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for key, url in URLS.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=url,
                document_version="Current official product page and embedded exact-model specification table; accessed 2026-10-15",
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"DrayTek Vigor{key} official product specifications",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        written = newly_filled = corrected = unchanged = status_corrected = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing DrayTek product: {model}")
            source = documents[item["source"]]
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
                    "source_url": source.url[:200],
                    "source_note": "Manually verified against the current DrayTek official product page and its exact-model specification table.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value)); new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value); new_value = bool(value)
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
                    product_spec=spec, source_document=source,
                    source_location=f"Official overview/specification table - {model} - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1

            # Earlier automated extraction mistook the page's 5G section header for a
            # built-in cellular standard. Keep the record, but remove the false value.
            if model in {"Vigor2927", "Vigor2962"}:
                cell_def = SpecDefinition.objects.filter(code="cellular_standard").first()
                false_spec = ProductSpec.objects.filter(product=product, definition=cell_def).first() if cell_def else None
                if false_spec and false_spec.value_status == ProductSpec.ValueStatus.PUBLISHED and false_spec.value_text == "5G":
                    false_spec.value_status = ProductSpec.ValueStatus.UNKNOWN
                    false_spec.value_text = ""
                    false_spec.value_number = None
                    false_spec.value_boolean = None
                    false_spec.normalized_value = ""
                    false_spec.raw_value = ""
                    false_spec.source_url = source.url[:200]
                    false_spec.source_note = "Corrected: prior 5G value was a specification-table header misparsed as a product capability."
                    false_spec.verified_date = accessed
                    false_spec.save()
                    status_corrected += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} false_values_cleared={status_corrected} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
