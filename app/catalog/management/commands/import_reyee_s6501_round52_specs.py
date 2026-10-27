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


MODEL = "S6501-48VS8CQ"
URL = "https://www.ruijie.com.cn/cp/jh-shjzhx-sjzxjr/s650148vs8cq/"
VALUES = {
    "jumbo_frame_bytes": n(9216, "L2协议：Jumbo Frame (9 Kbytes)"),
    "packet_buffer_mb": n(36, "产品特性：36MB缓存，轻松处理突发流量"),
    "stacking": t("VSU 2.0; M-LAG; de-stacking", "支持去堆叠、M-LAG和VSU 2.0虚拟化技术"),
    "dimensions_mm": t("442 x 387 x 44 mm (W x D x H)", "产品尺寸（宽x深x高）：442mm x 387mm x 44mm"),
    "max_power_consumption_w": n(268, "整机功耗：最大功耗268W"),
    "operating_temperature_c": t("0 to 45 °C", "工作环境温度：0°C~45°C"),
    "stp_features": t("STP, RSTP, MSTP", "L2协议：IEEE 802.1D (STP), IEEE 802.1w (RSTP), IEEE 802.1s (MSTP)"),
    "l2_features": t(
        "Static link aggregation; LACP; M-LAG; 802.1Q; STP/RSTP/MSTP; ERPS; IGMP/MLD snooping; QinQ; GVRP; LLDP",
        "L2协议包括静态链路聚合、LACP、跨设备链路聚合、802.1Q、STP/RSTP/MSTP、ERPS、IGMP/MLD Snooping、QinQ、GVRP和LLDP",
    ),
    "management_methods": t(
        "SNMP v1/v2c/v3; Telnet; console; MGMT; RMON; SSHv1/v2; FTP/TFTP; NTP; Syslog; SPAN/RSPAN/ERSPAN; Telemetry; ZTP; NETCONF; Python",
        "管理方式：SNMP v1/v2c/v3、Telnet、Console、MGMT、RMON、SSHv1/v2、FTP/TFTP、NTP、Syslog、SPAN/RSPAN/ERSPAN、Telemetry、ZTP、NETCONF、Python",
    ),
    "pbr_support": b(True, "L3协议（IPv4）：Policy-based Routing；IPv6特性：策略路由"),
    "ospf_support": b(True, "支持OSPFv2和OSPFv3"),
    "rip_support": b(True, "支持RIPv1、RIPv2和RIPng"),
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
    help = "Import exact current RG-S6501-48VS8CQ official product-page gaps (round 52)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=VALUES)}
        if not brand or set(VALUES) - definitions.keys():
            raise CommandError("Missing Reyee brand or required switch definitions")
        product = Product.objects.filter(brand=brand, model=MODEL, is_published=True).first()
        if not product:
            raise CommandError(f"Missing published Reyee product: {MODEL}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=URL,
            document_version="Current official product page and 2026 resource listing accessed 2026-10-21",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                "title": "Ruijie RG-S6501-48VS8CQ Official Product Page",
                "region": "China",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        written = new = corrected = unchanged = 0
        details = []
        for code, (kind, value, raw) in VALUES.items():
            definition = definitions[code]
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            old_value = actual(old)
            new_value = Decimal(str(value)) if kind == "number" else value
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": str(value) if kind == "text" else "",
                    "value_number": new_value if kind == "number" else None,
                    "value_boolean": bool(value) if kind == "boolean" else None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": URL[:200],
                    "source_note": "Manually verified from the current official exact-model Ruijie China product page.",
                    "verified_date": accessed,
                },
            )
            if old_value is None:
                new += 1
                detail = "+1"
            elif old_value != new_value:
                corrected += 1
                detail = "corrected:1"
            else:
                unchanged += 1
                detail = "unchanged:1"
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=source,
                source_location="技术参数 - 硬件规格与软件规格",
                defaults={
                    "source_excerpt": raw,
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            written += 1
            details.append(f"{code}:{detail}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models=1"
        ))
        self.stdout.write("; ".join(details))
