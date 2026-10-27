from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


REYEE = "https://reyee.ruijie.com/en-global/products"


PRODUCTS = {
    # Current EG product pages. "Throughput" is retained as routing throughput; NAT/VPN
    # throughput is not populated unless the official page explicitly labels it that way.
    "RG-EG105G": {
        "url": f"{REYEE}/reyee-router/eg-series/rg-eg105g-v2/",
        "location": "Highlights and Key Specifications",
        "values": {
            "controller_management": t("Ruijie Cloud and Ruijie Reyee App; self-organizing network and centralized management"),
            "lan_interfaces": t("3 fixed Gigabit LAN ports; 5 Gigabit Ethernet ports total"),
            "routing_throughput_mbps": n(600),
            "dimensions_mm": t("206.5 x 108.5 x 28 mm"),
        },
    },
    "RG-EG209GS": {
        "url": f"{REYEE}/reyee-router/eg-series/rg-eg209gs/",
        "location": "Models, features and Key Specifications",
        "values": {
            "controller_management": t("Ruijie Cloud and Ruijie Reyee App; centralized network management"),
            "lan_interfaces": t("5 fixed Gigabit LAN ports; 8 Gigabit Ethernet ports total"),
            "uplink_interfaces": t("1 x 1GbE SFP and 1 fixed Gigabit WAN port"),
            "routing_throughput_mbps": n(600),
            "dimensions_mm": t("202 x 108 x 28 mm"),
        },
    },
    "RG-EG210G-E": {
        "url": f"{REYEE}/reyee-router/eg-series/rg-eg210g-e/",
        "location": "Highlights and Key Specifications",
        "values": {
            "controller_management": t("Ruijie Cloud and Ruijie Reyee App; centralized network management"),
            "uplink_interfaces": t("1 fixed Gigabit WAN port; 10 Gigabit Ethernet ports total"),
            "routing_throughput_mbps": n(1000),
            "wan_load_balancing": b(),
            "firewall_features": t("Application blocking with automatically updated application library; captive portal"),
            "dimensions_mm": t("440 x 200 x 43.6 mm"),
        },
    },
    "RG-EG1510XS": {
        "url": f"{REYEE}/reyee-router/eg-series/eg1510xs/",
        "location": "Highlights, features and Key Specifications",
        "values": {
            "controller_management": t("Ruijie Cloud and Ruijie Reyee App; centralized network management"),
            "lan_interfaces": t("1 fixed LAN port; 4 x Gigabit and 4 x 2.5GbE RJ45 ports total"),
            "uplink_interfaces": t("1 fixed WAN port and 2 x 10GbE SFP+ ports"),
            "routing_throughput_mbps": n(4000),
            "vpn_tunnels": n(1000),
            "firewall_features": t("Application and user bandwidth management; captive portal authentication"),
            "dimensions_mm": t("440 x 210 x 43.6 mm"),
        },
    },
    "RG-EG406XS": {
        "url": f"{REYEE}/reyee-router/eg-series/rg-eg406xs/",
        "location": "Highlights and Key Specifications",
        "values": {
            "controller_management": t("Ruijie Cloud and Ruijie Reyee App; self-organizing network and centralized management"),
            "lan_interfaces": t("1 fixed LAN port; 5 x 2.5GbE RJ45 ports total"),
            "uplink_interfaces": t("1 fixed WAN port and 1 x 10GbE SFP+ port"),
            "routing_throughput_mbps": n(2500),
            "vpn_tunnels": n(100),
            "wan_load_balancing": b(),
            "dimensions_mm": t("202 x 108 x 28 mm"),
        },
    },
    "RG-EG710XS": {
        "url": f"{REYEE}/reyee-router/eg-series/rg-eg710xs/",
        "location": "Highlights and Key Specifications",
        "values": {
            "controller_management": t("Ruijie Cloud and Ruijie Reyee App; remote and centralized management"),
            "lan_interfaces": t("1 fixed LAN port; 4 x Gigabit and 4 x 2.5GbE RJ45 ports total"),
            "uplink_interfaces": t("1 fixed WAN port and 2 x 10GbE SFP+ ports"),
            "routing_throughput_mbps": n(3000),
            "vpn_tunnels": n(300),
            "wan_load_balancing": b(),
            "dimensions_mm": t("440 x 210 x 43.6 mm"),
        },
    },
    # AP values below are exact current-model values from official product pages.
    "RG-RAP2200(F)": {
        "url": f"{REYEE}/reyee-wireless/reyee-indoor-ap/rg-rap2200f/",
        "location": "Key Specifications",
        "values": {
            "ethernet_interfaces": t("2 x 10/100BASE-T"),
            "fast_roaming": t("Roaming supported"),
            "dimensions_mm": t("194 x 194 x 35 mm"),
        },
    },
    "RG-RAP2260": {
        "url": f"{REYEE}/reyee-wireless/reyee-indoor-ap/rg-rap2260/",
        "location": "Key Specifications",
        "values": {
            "ethernet_interfaces": t("1 x Gigabit Ethernet and 1 x 2.5GbE RJ45"),
            "fast_roaming": t("Roaming supported"),
            "dimensions_mm": t("194 x 194 x 45.1 mm"),
        },
    },
    "RG-RAP2260(H)": {
        "url": f"{REYEE}/reyee-wireless/reyee-indoor-ap/rg-rap2260h/",
        "location": "Models and Key Specifications",
        "values": {
            "ethernet_interfaces": t("2 x 2.5GbE RJ45"),
            "fast_roaming": t("Roaming supported"),
            "dimensions_mm": t("230 x 230 x 49.5 mm"),
        },
    },
    "RG-RAP62": {
        "url": f"{REYEE}/reyee-wireless/reyee-indoor-ap/rg-rap62/",
        "location": "Features and Key Specifications",
        "values": {
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T"),
            "fast_roaming": t("Roaming supported"),
            "dimensions_mm": t("Ø175 x 39 mm"),
        },
    },
    "RG-RAP62-OD": {
        "url": f"{REYEE}/reyee-wireless/reyee-outdoor-ap/rg-rap62-od/",
        "location": "Features and Key Specifications",
        "values": {
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T"),
            "fast_roaming": t("AI roaming and Reyee Mesh"),
            "dimensions_mm": t("70 x 35 x 200 mm"),
        },
    },
    "RG-RAP6262": {
        "url": f"{REYEE}/reyee-wireless/reyee-outdoor-ap/rap6262/",
        "location": "Key Specifications and installation guide V1.4",
        "values": {
            "fast_roaming": t("Roaming supported"),
            "dimensions_mm": t("Ø230 x 195 mm"),
        },
    },
    "RG-RAP6262(G)": {
        "url": f"{REYEE}/reyee-wireless/reyee-outdoor-ap/rg-rap6262g/",
        "location": "Key Specifications",
        "values": {
            "ethernet_interfaces": t("2 x 10/100/1000BASE-T"),
            "fast_roaming": t("Roaming supported"),
            "dimensions_mm": t("Ø200 x 166 mm"),
        },
    },
    "RG-RAP72Pro": {
        "url": f"{REYEE}/reyee-wireless/reyee-indoor-ap/rg-rap72pro/",
        "location": "Key Specifications",
        "values": {
            "fast_roaming": t("Roaming supported"),
            "dimensions_mm": t("208 x 208 x 40 mm"),
        },
    },
    "RG-RAP72Pro-OD": {
        "url": f"{REYEE}/reyee-wireless/reyee-outdoor-ap/rg-rap72pro-od/",
        "location": "Features and Key Specifications",
        "values": {
            "fast_roaming": t("AI roaming and mesh supported"),
            "dimensions_mm": t("90 x 46 x 239 mm"),
        },
    },
    # Wireless bridges: exact values from the current product pages and the current
    # official bridge implementation cookbook where the page refers to it.
    "RG-AirMetro460F": {
        "url": f"{REYEE}/reyee-wireless-bridge/airmetro-series/rg-airmetro460f/",
        "location": "Features, Key Specifications and applications",
        "values": {
            "rate_2g_mbps": n(150), "rate_5g_mbps": n(867),
            "wireless_range": t("Up to 15 km"), "antenna_gain_dbi": t("23 dBi"),
            "beamwidth": t("9° horizontal, 9° vertical"),
            "ethernet_interfaces": t("1 x 10/100 Mbps Ethernet"),
            "poe_input": t("1 x 24 V passive PoE input"),
            "bridge_modes": t("PTP and PTMP"), "max_bridge_pairs": n(32),
            "dimensions_mm": t("368.5 x 271 x 368.5 mm including mounting bracket"),
        },
    },
    "RG-AirMetro460G": {
        "url": f"{REYEE}/reyee-wireless-bridge/airmetro-series/rg-airmetro460g/",
        "location": "Features, Key Specifications and applications",
        "values": {
            "rate_2g_mbps": n(150), "rate_5g_mbps": n(867),
            "wireless_range": t("Up to 15 km"), "antenna_gain_dbi": t("23 dBi"),
            "beamwidth": t("9° horizontal, 9° vertical"),
            "ethernet_interfaces": t("1 x 10/100/1000 Mbps Ethernet"),
            "poe_input": t("1 x 24 V passive PoE input"),
            "bridge_modes": t("PTP and PTMP"), "max_bridge_pairs": n(32),
            "dimensions_mm": t("368.5 x 271 x 368.5 mm including mounting bracket"),
        },
    },
    "RG-AirMetro550G-B": {
        "url": f"{REYEE}/reyee-wireless-bridge/airmetro-series/airmetro550g-b/",
        "location": "Highlights and Key Specifications",
        "values": {
            "rate_2g_mbps": n(150), "rate_5g_mbps": n(867),
            "wireless_range": t("Up to 10 km, depending on attached official antenna"),
            "ethernet_interfaces": t("2 x Gigabit Ethernet"),
            "poe_input": t("1 x 24 V passive PoE input; 12 V DC also supported"),
            "bridge_modes": t("PTMP base station"), "max_bridge_pairs": n(32),
            "dimensions_mm": t("98.5 x 29 x 200 mm excluding mounting bracket"),
        },
    },
    "RG-EST100-E": {
        "url": f"{REYEE}/reyee-wireless-bridge/est-series/est100/",
        "location": "Key Specifications and applications",
        "values": {
            "wireless_range": t("Up to 500 m"),
            "beamwidth": t("70° horizontal, 70° vertical"),
            "ethernet_interfaces": t("1 x Fast Ethernet"),
            "poe_input": t("1 x PoE input"), "bridge_modes": t("PTP"),
            "ip_rating": t("IP55"), "antenna_type": t("Built-in directional antenna"),
            "dimensions_mm": t("68.7 x 42 x 165.5 mm"),
            "operating_temperature_c": t("-30 to 60 °C"),
        },
    },
    "RG-EST310": {
        "url": f"{REYEE}/reyee-wireless-bridge/est-series/rg-est310v2/",
        "location": "Features, Key Specifications and order information",
        "values": {
            "rate_5g_mbps": n(867), "wireless_range": t("1 km rated; official performance table includes up to 3 km"),
            "beamwidth": t("60° horizontal, 30° vertical"),
            "ethernet_interfaces": t("1 x 10/100 Mbps Ethernet"),
            "poe_input": t("24 V passive PoE input"), "bridge_modes": t("PTP and PTMP"),
            "ip_rating": t("IP54"), "dimensions_mm": t("76 x 37 x 147 mm excluding mounting bracket"),
        },
    },
    "RG-EST350": {
        "url": f"{REYEE}/reyee-wireless-bridge/rg-est350v2/",
        "location": "Features, Key Specifications and applications",
        "values": {
            "rate_5g_mbps": n(867), "wireless_range": t("Up to 5 km"),
            "ethernet_interfaces": t("2 x Gigabit Ethernet"),
            "poe_input": t("1 x PoE input"), "bridge_modes": t("PTP and PTMP"),
            "ip_rating": t("IP54"),
        },
    },
    "RG-EST350G": {
        "url": f"{REYEE}/reyee-wireless-bridge/est-series/rg-est350g/",
        "location": "Features and Key Specifications",
        "values": {
            "rate_2g_mbps": n(150), "rate_5g_mbps": n(867), "wireless_range": t("Up to 5 km"),
            "antenna_gain_dbi": t("16 dBi"), "beamwidth": t("31° horizontal, 14° vertical"),
            "ethernet_interfaces": t("3 x Gigabit Ethernet"),
            "bridge_modes": t("PTP and PTMP"),
            "dimensions_mm": t("133 x 108 x 240 mm excluding mounting bracket"),
        },
    },
    "RG-EST450G": {
        "url": f"{REYEE}/reyee-wireless-bridge/est-series/rg-est450g/",
        "location": "Features and Key Specifications",
        "values": {
            "rate_2g_mbps": n(150), "rate_5g_mbps": n(867), "wireless_range": t("Up to 5 km with compatible CPE"),
            "antenna_gain_dbi": t("15 dBi"), "beamwidth": t("120° horizontal, 13° vertical"),
            "ethernet_interfaces": t("3 x Gigabit Ethernet"),
            "bridge_modes": t("PTMP station; one-touch pairing"),
            "dimensions_mm": t("124 x 48 x 355 mm excluding mounting bracket"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee priority specifications (round 11)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        written = newly_filled = corrected = unchanged = 0
        missing_models = []
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            source, _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Current official product page, accessed 2026-10-14",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"Reyee {model} official product page", "region": "Global",
                    "published_date": None, "accessed_date": accessed, "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had_value = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None
                ))
                old_value = None
                if had_value:
                    old_value = existing.value_text if existing.value_text else existing.value_number if existing.value_number is not None else existing.value_boolean
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "",
                    "value_number": None, "value_boolean": None, "normalized_value": str(value),
                    "unit": definition.unit, "raw_value": str(value), "source_url": source.url[:200],
                    "source_note": "Manually verified from the current official Reyee exact-model product page and linked official technical material.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value)); new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value); new_value = bool(value)
                else:
                    defaults["value_text"] = str(value); new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had_value:
                    newly_filled += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location=f"{item['location']} - {model}",
                    defaults={"source_excerpt": f"{definition.display_name}: {value}",
                              "evidence_level": SpecEvidence.EvidenceLevel.A,
                              "verified_at": timezone.now()},
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)-len(missing_models)}"
        ))
        self.stdout.write("; ".join(per_model))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
