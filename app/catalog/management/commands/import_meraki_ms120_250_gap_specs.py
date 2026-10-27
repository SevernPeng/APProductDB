from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


MS120 = (
    "MS120-24-HW", "MS120-24P-HW", "MS120-48-HW", "MS120-48LP-HW",
    "MS120-8-HW", "MS120-8FP-HW", "MS120-8LP-HW",
)
MS125 = ("MS125-24-HW", "MS125-24P-HW", "MS125-48FP-HW")
MS225 = ("MS225-24-HW", "MS225-24P-HW", "MS225-48-HW", "MS225-48FP-HW")
MS250 = ("MS250-24-HW", "MS250-24P-HW", "MS250-48-HW", "MS250-48FP-HW")
ALL_MODELS = MS120 + MS125 + MS225 + MS250

URLS = {
    "MS120": "https://documentation.meraki.com/Switching/MS_-_Switches/Product_Information/Overviews_and_Datasheets/MS120_Datasheet",
    "MS125": "https://documentation.meraki.com/Switching/MS_-_Switches/Product_Information/Overviews_and_Datasheets/MS125_Datasheet",
    "MS125_INSTALL": "https://documentation.meraki.com/Switching/MS_-_Switches/Install_and_Get_Started/Installation_Guides/MS125_Series_Installation_Guide",
    "MS225": "https://documentation.meraki.com/Switching/MS_-_Switches/Product_Information/Overviews_and_Datasheets/MS225_Datasheet",
    "MS250": "https://documentation.meraki.com/Switching/MS_-_Switches/Product_Information/Overviews_and_Datasheets/MS250_Datasheet",
    "STACK": "https://documentation.meraki.com/Switching/MS_-_Switches/Design_and_Configure/Architecture_and_Best_Practices/Switch_Stacks",
    "SETTINGS": "https://documentation.meraki.com/Switching/MS_-_Switches/Operate_and_Maintain/How-Tos/Switch_Settings",
    "STP": "https://documentation.meraki.com/Switching/MS_-_Switches/Design_and_Configure/Configuration_Guides/Port_and_VLAN_Configuration/Configuring_Spanning_Tree_on_Meraki_Switches_(MS)",
    "L3": "https://documentation.meraki.com/Switching/MS_-_Switches/Design_and_Configure/Configuration_Guides/Layer_3_Switching/MS_Layer_3_Switching_and_Routing",
    "POE": "https://documentation.meraki.com/MR/Monitoring_and_Reporting/Low_Power_Mode",
}

TITLES = {
    "MS120": "Cisco Meraki MS120 Datasheet",
    "MS125": "Cisco Meraki MS125 Datasheet",
    "MS125_INSTALL": "Cisco Meraki MS125 Series Installation Guide",
    "MS225": "Cisco Meraki MS225 Datasheet",
    "MS250": "Cisco Meraki MS250 Datasheet",
    "STACK": "Cisco Meraki Switch Stacks",
    "SETTINGS": "Cisco Meraki Switch Settings",
    "STP": "Configuring Spanning Tree on Meraki Switches (MS)",
    "L3": "Cisco Meraki MS Layer 3 Switching and Routing",
    "POE": "Cisco Meraki Low Power Mode and PoE Negotiation",
}


ITEMS = []


def add(models, code, kind, value, raw, source, location):
    for model in models:
        ITEMS.append({
            "model": model,
            "code": code,
            "kind": kind,
            "value": value,
            "raw": raw,
            "url": URLS[source],
            "title": TITLES[source],
            "location": location,
        })


# Current family datasheets explicitly publish these management, L2 and security features.
for family, models in (("MS120", MS120), ("MS125", MS125), ("MS225", MS225), ("MS250", MS250)):
    add(
        models, "management_methods", "text",
        "Cisco Meraki Dashboard; remote packet capture; SNMP/Syslog integration",
        "Managed via Cisco Meraki Dashboard; Remote Packet Capture Tools via Meraki Dashboard; SNMP/Syslog integration",
        family, "Features",
    )
    if family in ("MS120", "MS125"):
        l2 = "802.1Q VLAN tagging; DHCP snooping; 802.1X authentication"
        l2_raw = "802.1Q VLAN tagging; DHCP snooping; 802.1X authentication"
    else:
        l2 = "802.1Q VLAN tagging; broadcast storm control; Dynamic ARP Inspection; DHCP snooping; 802.1X authentication"
        l2_raw = "802.1Q VLAN tagging; Broadcast Storm Control; Dynamic ARP Inspection / DHCP Snooping; 802.1X Authentication"
    add(models, "l2_features", "text", l2, l2_raw, family, "Features")
    add(
        models, "acl_security", "text", "IPv4/IPv6 ACL support",
        "IPv4/6 Access Control List (ACL) support", family, "Features",
    )
    add(
        models, "vlan_count", "number", 4094,
        "802.1Q VLAN and trunking support for up to 4,094 VLANs",
        family, "Ethernet Switching Capabilities",
    )

# Cisco's current MS configuration references cover all of these classic MS families.
add(
    ALL_MODELS, "jumbo_frame_bytes", "number", 9578,
    "The maximum MTU on MS classic switches is 9578 bytes.",
    "SETTINGS", "MTU Configuration",
)
add(
    ALL_MODELS, "stp_features", "text",
    "IEEE 802.1D STP; IEEE 802.1w RSTP (enabled by default); Root Guard; BPDU Guard; Loop Guard",
    "The MS series supports IEEE 802.1D STP and IEEE 802.1w RSTP; RSTP is enabled by default; Root, BPDU and Loop guard are configurable.",
    "STP", "Spanning Tree and port-level STP guard configuration",
)

# The live compatibility table explicitly distinguishes unsupported and supported stacking.
add(
    MS120, "stacking", "text", "Physical stacking: No; flexible stacking: No",
    "MS120 — Physical Stacking: No; Flexible Stacking: No", "STACK", "Stacking Availability",
)
add(
    MS125, "stacking", "text", "Physical stacking: No; flexible stacking: No",
    "MS125 — Physical Stacking: No; Flexible Stacking: No", "STACK", "Stacking Availability",
)
add(
    MS225, "stacking", "text", "Physical stacking: Yes (compatible with MS210); flexible stacking: No",
    "MS225 — Physical Stacking: Yes (Compatible with MS210); Flexible Stacking: No", "STACK", "Stacking Availability",
)
add(
    MS250, "stacking", "text", "Physical stacking: Yes; flexible stacking: No",
    "MS250 — Physical Stacking: Yes; Flexible Stacking: No", "STACK", "Stacking Availability",
)
add(
    MS225, "stacking_bandwidth_gbps", "number", 80,
    "2 dedicated stack ports providing 80 Gbps of stacking bandwidth", "MS225", "Features and Throughput and Capabilities",
)
add(
    MS250, "stacking_bandwidth_gbps", "number", 80,
    "2 dedicated stack ports providing 80 Gbps of stacking bandwidth", "MS250", "Features and Throughput and Capabilities",
)

# PoE/PoE+ is stated per family/model; Cisco's PoE standards table defines PoE+ as 802.3at up to 30 W.
POE_MODELS = {
    "MS120": {"MS120-24P-HW": 24, "MS120-48LP-HW": 48, "MS120-8FP-HW": 8, "MS120-8LP-HW": 8},
    "MS125": {"MS125-24P-HW": 24, "MS125-48FP-HW": 48},
    "MS225": {"MS225-24P-HW": 24, "MS225-48FP-HW": 48},
    "MS250": {"MS250-24P-HW": 24, "MS250-48FP-HW": 48},
}
for family, model_ports in POE_MODELS.items():
    for model, ports in model_ports.items():
        add((model,), "poe_ports", "number", ports, f"{ports} 1GbE RJ45 ports; model is PoE/PoE+ capable", family, "Hardware and PoE capabilities")
        add((model,), "poe_standard", "text", "IEEE 802.3af PoE / 802.3at PoE+", "PoE and PoE+ capable", family, "Features and PoE capabilities")
        add((model,), "max_poe_per_port_w", "number", 30, "PoE+ — IEEE 802.3at — up to 30 W", "POE", "PoE Standards")

# Power-supply construction and cooling that are explicitly shown in current hardware tables.
add(("MS120-24-HW", "MS120-24P-HW", "MS120-48-HW", "MS120-48LP-HW"), "power_supply", "text", "Fixed internal power supply", "Power Supply: Fixed Internal", "MS120", "Throughput and Capabilities")
add(("MS120-8FP-HW",), "power_supply", "text", "Fixed internal power supply", "Power Supply: Fixed Internal", "MS120", "Throughput and Capabilities — MS120-8 models")
add(("MS120-8LP-HW",), "power_supply", "text", "External power supply", "Power Supply: External", "MS120", "Throughput and Capabilities — MS120-8 models")
add(("MS120-8-HW",), "fan_design", "text", "Fanless", "Fanless operation", "MS120", "Specifications — Environment (MS120-8 compact series)")
add(MS125, "power_supply", "text", "Built-in power supply", "Power Supply: Built-in", "MS125", "Throughput and Capabilities")
add(("MS125-24-HW",), "fan_design", "text", "Fanless", "Fans: -", "MS125_INSTALL", "Product Overview — Physical Specifications")
add(("MS125-24P-HW", "MS125-48FP-HW"), "fan_design", "text", "Built-in fans", "Fans: Built-in", "MS125_INSTALL", "Product Overview — Physical Specifications")
add(MS125, "operating_temperature_c", "text", "0 to 45 °C", "Operating Temperature: 0°C - 45°C", "MS125", "Physical")

# Official routing scale table for MS225 and MS250.
add(MS225, "routing_entry_capacity", "text", "16 static routes", "MS225: 16 static routes", "L3", "Supported Models — routing scale table")
add(MS250, "ip_interface_capacity", "text", "256 Layer 3 interfaces", "MS250: 256 Layer 3 interfaces", "L3", "Supported Models — routing scale table")
add(MS250, "routing_entry_capacity", "text", "1024 routes (256 static; up to 900 learned OSPF routes)", "MS250: 1024 routes (256 static routes); maximum learned OSPF routes: 900", "L3", "Supported Models — routing scale table and note 1")
add(MS250, "ospf_support", "boolean", True, "MS250 supported features include OSPFv2", "L3", "Supported Models — routing scale table")


class Command(BaseCommand):
    help = "Import manually verified Cisco Meraki MS120/MS125/MS225/MS250 gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Meraki").first()
        if not brand:
            raise CommandError("Missing brand: Meraki")
        codes = {item["code"] for item in ITEMS}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        newly_filled = corrected = unchanged = 0
        for item in ITEMS:
            doc_key = item["url"]
            if doc_key not in documents:
                documents[doc_key], _ = SourceDocument.objects.update_or_create(
                    url=item["url"], document_version="Current official web documentation; accessed 2026-10-20",
                    defaults={
                        "brand": brand, "product": None,
                        "document_type": SourceDocument.DocumentType.SPECIFICATION,
                        "title": item["title"], "region": "Global", "published_date": None,
                        "accessed_date": accessed, "active": True,
                    },
                )
            product = Product.objects.filter(brand=brand, model=item["model"], is_published=True).first()
            if not product:
                raise CommandError(f"Missing Meraki product: {item['model']}")
            definition = definitions[item["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None
            ))
            if item["kind"] == "number":
                old_value = existing.value_number if had else None
                new_value = Decimal(str(item["value"]))
            elif item["kind"] == "boolean":
                old_value = existing.value_boolean if had else None
                new_value = bool(item["value"])
            else:
                old_value = existing.value_text if had else None
                new_value = str(item["value"])

            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "", "value_number": None, "value_boolean": None,
                "normalized_value": str(item["value"]), "unit": definition.unit,
                "raw_value": item["raw"], "source_url": item["url"][:200],
                "source_note": "Manually verified from current official Cisco Meraki documentation.",
                "verified_date": accessed,
            }
            if item["kind"] == "number":
                defaults["value_number"] = new_value
            elif item["kind"] == "boolean":
                defaults["value_boolean"] = new_value
            else:
                defaults["value_text"] = new_value
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had:
                newly_filled += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=documents[doc_key], source_location=item["location"],
                defaults={
                    "source_excerpt": item["raw"], "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"
        ))
