from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import (
    Brand,
    Product,
    ProductSpec,
    SourceDocument,
    SpecDefinition,
    SpecEvidence,
)


SOURCES = {
    "revf": {
        "url": "https://support.dlink.com/resource/products/DGS-1210-SERIES/REVF/DGS-1210_Series_REVF_DATASHEET_v14_WW.pdf",
        "title": "D-Link DGS-1210 Series 1G Smart Managed Switches Datasheet",
        "version": "Rev F v14 WW",
        "published": None,
    },
    "me": {
        "url": "https://meweb.dlink.com/en/-/media/business_products/dgs/dgs-1210/datasheet/dgs1210meseriesdatasheetv1000ww.pdf",
        "title": "D-Link DGS-1210ME Series Metro Ethernet Switches Datasheet",
        "version": "v1000WW",
        "published": date(2017, 5, 23),
    },
}


BASE_SOFTWARE = {
    "management_methods": (
        "text",
        "Web GUI; D-Link Network Assistant; compact CLI/Telnet; SNMP v1/v2c/v3; "
        "D-View 8; Nuclias Unity/controller",
    ),
    "vlan_count": ("number", 256),
    "l2_features": (
        "text",
        "IGMP/MLD snooping; IEEE 802.3ad link aggregation; LLDP/LLDP-MED; "
        "port mirroring; loopback detection; 802.1Q VLAN",
    ),
    "stp_features": ("text", "IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
    "acl_security": (
        "text",
        "MAC/IPv4/IPv6 ACLs; up to 50 access lists and 768 shared entries; "
        "802.1X; port security; DHCP snooping; ARP spoofing prevention",
    ),
    "jumbo_frame_bytes": ("number", 10000),
}


ME_SOFTWARE = {
    "management_methods": (
        "text",
        "Web GUI; CLI; Telnet; TFTP; SNMP v1/v2c/v3; RMON; system log; LLDP",
    ),
    "vlan_count": ("number", 4094),
    "l2_features": (
        "text",
        "IEEE 802.3ad link aggregation; IGMP/MLD snooping; L2 protocol tunneling; "
        "port mirroring; loopback detection; 802.1Q/GVRP/Q-in-Q/private VLAN",
    ),
    "stp_features": (
        "text",
        "IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU filtering; root restriction",
    ),
    "acl_security": (
        "text",
        "MAC/IPv4/IPv6 ACLs; up to 256 ingress rules; time-based ACL; 802.1X; "
        "IP-MAC-Port Binding; DHCP snooping; DoS prevention",
    ),
    "jumbo_frame_bytes": ("number", 9216),
}


def hardware(
    interfaces,
    capacity,
    forwarding,
    mac,
    buffer_mb,
    power,
    fan,
    max_power,
    dimensions,
    *,
    dram,
):
    return {
        "ethernet_interfaces": ("text", interfaces),
        "switching_capacity_gbps": ("number", capacity),
        "packet_forwarding_rate_mpps": ("number", forwarding),
        "mac_address_table": ("text", f"{mac:,} entries"),
        "packet_buffer_mb": ("number", buffer_mb),
        "power_supply": ("text", power),
        "fan_design": ("text", fan),
        "max_power_consumption_w": ("number", max_power),
        "dimensions_mm": ("text", dimensions),
        "operating_temperature_c": ("text", "-5 to 50 °C"),
        "dram_memory": ("text", dram),
        "flash_memory": ("text", "32 MB"),
    }


def poe(ports, budget):
    return {
        "poe_configuration": ("text", f"{ports} PoE+ ports; {budget} W total budget"),
        "poe_standard": ("text", "IEEE 802.3af/at"),
        "poe_ports": ("number", ports),
        "poe_budget_w": ("number", budget),
        "max_poe_per_port_w": ("number", 30),
    }


MODELS = {
    "DGS-1210-10": (
        "revf",
        {
            **hardware("8 x 10/100/1000BASE-T; 2 x 100/1000 Mbps SFP", 20, 14.88, 8000, 0.513, "100-240 V AC, 50/60 Hz", "Fanless", 6.33, "280 x 126 x 44 mm", dram="128 MB"),
            **BASE_SOFTWARE,
        },
        False,
        "Technical specifications - DGS-1210-10 (Fx), pages 3 and 7-8",
    ),
    "DGS-1210-10P": (
        "revf",
        {
            **hardware("8 x 10/100/1000BASE-T PoE; 2 x 100/1000 Mbps SFP", 20, 14.88, 8000, 0.513, "54 V DC external power adapter", "Fanless", 81.9, "280 x 126 x 44 mm", dram="128 MB"),
            **BASE_SOFTWARE,
            **poe(8, 65),
        },
        True,
        "Technical specifications - DGS-1210-10P (Fx), pages 5 and 7-8",
    ),
    "DGS-1210-20": (
        "revf",
        {
            **hardware("16 x 10/100/1000BASE-T; 4 x 100/1000 Mbps GbE/SFP combo", 40, 29.8, 8000, 0.513, "100-240 V AC, 50/60 Hz", "Fanless", 13.08, "280 x 180 x 44 mm", dram="128 MB"),
            **BASE_SOFTWARE,
        },
        False,
        "Technical specifications - DGS-1210-20 (Fx), pages 3 and 7-8",
    ),
    "DGS-1210-28": (
        "revf",
        {
            **hardware("24 x 10/100/1000BASE-T; 4 x 100/1000 Mbps GbE/SFP combo", 56, 41.7, 8000, 0.513, "100-240 V AC, 50/60 Hz", "Fanless", 17.32, "440 x 140 x 44 mm", dram="128 MB"),
            **BASE_SOFTWARE,
        },
        False,
        "Technical specifications - DGS-1210-28 (Fx), pages 3 and 7-8",
    ),
    "DGS-1210-28MP": (
        "revf",
        {
            **hardware("24 x 10/100/1000BASE-T PoE; 4 x 100/1000 Mbps GbE/SFP combo", 56, 41.7, 8000, 0.513, "100-240 V AC, 50/60 Hz", "2 fans", 446.1, "440 x 250 x 44 mm", dram="128 MB"),
            **BASE_SOFTWARE,
            **poe(24, 370),
        },
        True,
        "Technical specifications - DGS-1210-28MP (Fx), pages 6-8",
    ),
    "DGS-1210-52": (
        "revf",
        {
            **hardware("48 x 10/100/1000BASE-T; 4 x 100/1000 Mbps GbE/SFP combo", 104, 77.4, 16000, 1.5, "100-240 V AC, 50/60 Hz", "Fanless", 34.85, "440 x 210 x 44 mm", dram="128 MB"),
            **BASE_SOFTWARE,
        },
        False,
        "Technical specifications - DGS-1210-52 (Fx), pages 4 and 7-8",
    ),
    "DGS-1210-52MP": (
        "revf",
        {
            **hardware("48 x 10/100/1000BASE-T PoE; 4 x 100/1000 Mbps GbE/SFP combo", 104, 77.4, 16000, 1.5, "100-240 V AC, 50/60 Hz", "3 fans", 478.9, "440 x 430 x 44 mm", dram="128 MB"),
            **BASE_SOFTWARE,
            **poe(48, 370),
        },
        True,
        "Technical specifications - DGS-1210-52MP (Fx), pages 6-8",
    ),
    "DGS-1210-10/ME": (
        "me",
        {
            **hardware("8 x 10/100/1000BASE-T; 2 x 1G SFP", 20, 14.88, 16000, 1.5, "100-240 V AC, 50/60 Hz", "Fanless", 13.59, "280 x 126 x 44 mm", dram="256 MB DDR3"),
            **ME_SOFTWARE,
        },
        False,
        "Technical specifications - DGS-1210-10/ME (B1), pages 6-10",
    ),
    "DGS-1210-28/ME": (
        "me",
        {
            **hardware("24 x 10/100/1000BASE-T; 4 x 1G SFP", 56, 41.7, 16000, 1.5, "100-240 V AC, 50/60 Hz", "Fanless", 19.14, "440 x 140 x 44 mm", dram="256 MB DDR3"),
            **ME_SOFTWARE,
        },
        False,
        "Technical specifications - DGS-1210-28/ME (B1), pages 6-10",
    ),
    "DGS-1210-28MP/ME": (
        "me",
        {
            **hardware("24 x 10/100/1000BASE-T PoE; 4 x 1G SFP", 56, 41.7, 16000, 1.5, "100-240 V AC, 50/60 Hz", "3 smart fans", 445, "440 x 250 x 44 mm", dram="256 MB DDR3"),
            **ME_SOFTWARE,
            **poe(24, 370),
        },
        True,
        "Technical specifications - DGS-1210-28MP/ME (B1), pages 3-4 and 9-10",
    ),
    "DGS-1210-28XS/ME": (
        "me",
        {
            **hardware("24 x 100/1000 Mbps SFP; 4 x 10G SFP+", 128, 95.24, 16000, 1.5, "100-240 V AC, 50/60 Hz", "2 smart fans", 33.4, "440 x 210 x 44 mm", dram="256 MB DDR3"),
            "fanless": ("boolean", False),
            **ME_SOFTWARE,
        },
        False,
        "Technical specifications - DGS-1210-28XS/ME (B1), pages 7-10",
    ),
    "DGS-1210-52/ME": (
        "me",
        {
            **hardware("48 x 10/100/1000BASE-T; 4 x 1G SFP", 104, 77.4, 16000, 3, "100-240 V AC, 50/60 Hz", "1 smart fan", 38.85, "440 x 210 x 44 mm", dram="256 MB DDR3"),
            **ME_SOFTWARE,
        },
        False,
        "Technical specifications - DGS-1210-52/ME (B1), pages 6-10",
    ),
    "DGS-1210-52MP/ME": (
        "me",
        {
            **hardware("48 x 10/100/1000BASE-T PoE; 4 x 1G SFP", 104, 77.4, 16000, 3, "100-240 V AC, 50/60 Hz", "3 smart fans", 479.5, "440 x 430 x 44 mm", dram="256 MB DDR3"),
            **ME_SOFTWARE,
            **poe(48, 370),
        },
        True,
        "Technical specifications - DGS-1210-52MP/ME (B1), pages 4-5 and 9-10",
    ),
}

# The catalog's normalized model omits the regional "/ME" suffix, while its
# retained official URL and physical attributes identify the same live product.
MODELS["DGS-1210-28XS"] = (
    "me",
    MODELS["DGS-1210-28XS/ME"][1],
    False,
    "Technical specifications - DGS-1210-28XS/ME (B1), pages 7-10; catalog alias without /ME suffix",
)


POE_CODES = {
    "poe_configuration",
    "poe_standard",
    "poe_ports",
    "poe_budget_w",
    "max_poe_per_port_w",
}


class Command(BaseCommand):
    help = "Import manually verified D-Link DGS-1210 Rev F and DGS-1210/ME specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Brand 'D-Link' was not found.")

        codes = {code for _, values, _, _ in MODELS.values() for code in values} | POE_CODES
        definitions = {
            definition.code: definition
            for definition in SpecDefinition.objects.filter(code__in=codes)
        }
        missing_definitions = codes - definitions.keys()
        if missing_definitions:
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing_definitions))}")

        accessed = timezone.localdate()
        sources = {}
        for key, metadata in SOURCES.items():
            source, _ = SourceDocument.objects.update_or_create(
                url=metadata["url"],
                document_version=metadata["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": metadata["title"],
                    "region": "Global" if key == "revf" else "Middle East / Global ME series",
                    "published_date": metadata["published"],
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            sources[key] = source

        updated = 0
        marked_not_applicable = 0
        missing_models = []
        for model, (source_key, values, is_poe, location) in MODELS.items():
            product = Product.objects.filter(
                brand=brand,
                model=model,
                is_published=True,
            ).first()
            if not product:
                missing_models.append(model)
                continue
            source = sources[source_key]
            for code, (kind, value) in values.items():
                definition = definitions[code]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": str(value),
                    "source_url": source.url[:200],
                    "source_note": f"Manually verified from official D-Link {source.document_version} datasheet.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                else:
                    defaults["value_text"] = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=location,
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {value}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

            if not is_poe:
                for code in POE_CODES:
                    definition = definitions[code]
                    spec, _ = ProductSpec.objects.update_or_create(
                        product=product,
                        definition=definition,
                        defaults={
                            "value_status": ProductSpec.ValueStatus.NOT_APPLICABLE,
                            "value_text": "",
                            "value_number": None,
                            "value_boolean": None,
                            "normalized_value": "",
                            "unit": definition.unit,
                            "raw_value": "Not a PoE model",
                            "source_url": source.url[:200],
                            "source_note": f"Official {source.document_version} interface table identifies this as a non-PoE model.",
                            "verified_date": accessed,
                        },
                    )
                    SpecEvidence.objects.update_or_create(
                        product_spec=spec,
                        source_document=source,
                        source_location=location,
                        defaults={
                            "source_excerpt": "Model interface/PoE table: non-PoE model",
                            "evidence_level": SpecEvidence.EvidenceLevel.A,
                            "verified_at": timezone.now(),
                        },
                    )
                    marked_not_applicable += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={updated} not_applicable={marked_not_applicable} "
                f"models={len(MODELS) - len(missing_models)}"
            )
        )
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
