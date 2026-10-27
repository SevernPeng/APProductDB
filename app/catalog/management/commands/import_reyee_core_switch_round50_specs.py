from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw):
    return "number", value, raw


def t(value, raw):
    return "text", value, raw


def b(value, raw):
    return "boolean", value, raw


PRODUCTS = {
    "RG-S6120-20XS4VS2QXS": {
        "url": "https://www.ruijie.com/en-global/products/switches/campus-switches/rg-s6120-20xs4vs2qxs",
        "values": {
            "jumbo_frame_bytes": n(9216, "Jumbo frame (maximum length): 9,216 bytes"),
            "stacking": t("VSU virtualization supported", "Device virtualization: VSU"),
            "stacking_bandwidth_gbps": n(200, "VSU bandwidth: 200 Gbps"),
            "dimensions_mm": t("440 x 330 x 43.6 mm (W x D x H)", "Unit dimensions (W x D x H): 440 mm x 330 mm x 43.6 mm"),
            "routing_entry_capacity": t(
                "IPv4 unicast: 16,000; IPv6 unicast: 8,000; IPv4 multicast: 4,000; IPv6 multicast: 2,000",
                "Maximum routes: IPv4 unicast 16,000; IPv6 unicast 8,000; IPv4 multicast 4,000; IPv6 multicast 2,000",
            ),
            "stp_features": t("STP, RSTP, MSTP", "STP (IEEE 802.1d), RSTP (IEEE 802.1w), and MSTP (IEEE 802.1s)"),
            "vlan_count": n(4094, "Maximum number of VLANs that can be created: 4,094"),
            "ip_interface_capacity": t("1,000 SVIs", "Maximum number of SVIs: 1,000"),
            "l2_features": t(
                "802.1Q VLAN; voice VLAN; super/private VLAN; GVRP; QinQ; STP/RSTP/MSTP; ERPS; LACP; LLDP/LLDP-MED",
                "Ethernet Switching includes 802.1Q VLAN, voice VLAN, super/private VLAN, GVRP, QinQ, STP/RSTP/MSTP, ERPS, LACP, and LLDP/LLDP-MED",
            ),
            "management_methods": t(
                "CLI (console/Telnet); SNMP v1/v2/v3; RMON; NETCONF; gRPC; CWMP; sFlow; FTP/TFTP; RG-UNC",
                "NMS and maintenance: CLI, SNMP v1/v2/v3, RMON, NETCONF, gRPC, CWMP, sFlow, FTP/TFTP; RG-UNC unified management",
            ),
            "pbr_support": b(True, "IPv4/IPv6 PBR"),
            "ospf_support": b(True, "OSPFv2 and OSPFv3"),
            "rip_support": b(True, "RIP and RIPng"),
        },
    },
    "RG-CS86-20XS4VS2QXS-D": {
        "url": "https://www.ruijie.com/en-global/products/switches/campus-switches/rg-cs86-20xs4vs2qxs-d",
        "values": {
            "jumbo_frame_bytes": n(9216, "Jumbo frame (maximum length): 9,216 bytes"),
            "vlan_count": n(4094, "IEEE 802.1Q (supporting 4K VLANs)"),
            "stacking": t("VSU virtualization supported", "Device virtualization: VSU; number of VSU members: 2"),
            "dimensions_mm": t("440 x 330 x 43.6 mm (W x D x H)", "Unit dimensions (W x D x H): 440 mm x 330 mm x 43.6 mm"),
            "routing_entry_capacity": t(
                "IPv4 unicast: 16,000; IPv6 unicast: 16,000; IPv4 multicast: 4,000; IPv6 multicast: 2,000",
                "Routes: IPv4 unicast 16,000; IPv6 unicast 16,000; IPv4 multicast 4,000; IPv6 multicast 2,000",
            ),
            "stp_features": t("STP, RSTP, MSTP", "Ethernet Switching: STP, RSTP, and MSTP"),
            "l2_features": t(
                "802.1Q VLAN; voice VLAN; super/private VLAN; GVRP; QinQ; STP/RSTP/MSTP; ERPS; LACP; LLDP/LLDP-MED",
                "Ethernet Switching includes 802.1Q VLAN, voice VLAN, super/private VLAN, GVRP, QinQ, STP/RSTP/MSTP, ERPS, LACP, and LLDP/LLDP-MED",
            ),
            "management_methods": t(
                "Ruijie Cloud/SON; SNMP v1/v2/v3; RMON; Telnet; NETCONF; gRPC; CWMP; sFlow; FTP/TFTP",
                "NMS and maintenance: Ruijie Cloud and SON, SNMP v1/v2/v3, RMON, Telnet, NETCONF, gRPC, CWMP, sFlow, FTP/TFTP",
            ),
            "pbr_support": b(True, "IPv4 and IPv6 PBR"),
            "ospf_support": b(True, "OSPFv2 and OSPFv3"),
            "rip_support": b(True, "RIP and RIPng"),
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
    help = "Import exact current Ruijie core-switch product-page gaps (round 50)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if not brand or codes - definitions.keys():
            raise CommandError("Missing Reyee brand or required core-switch definitions")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version="Current official product page accessed 2026-10-21",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"Ruijie {model} Official Product Page",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = actual(old)
                new_value = Decimal(str(value)) if kind == "number" else value
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": str(value) if kind == "text" else "",
                    "value_number": new_value if kind == "number" else None,
                    "value_boolean": bool(value) if kind == "boolean" else None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": row["url"][:200],
                    "source_note": "Manually verified from the current official exact-model product specification table.",
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
                    source_location="Hardware and Software Specifications",
                    defaults={
                        "source_excerpt": raw,
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
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
