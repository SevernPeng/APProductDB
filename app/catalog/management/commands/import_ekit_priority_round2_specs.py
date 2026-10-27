from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


SECURITY = (
    "WEP; WPA2-PSK; WPA2-802.1X; WPA3-SAE; WPA3-802.1X; "
    "WPA/WPA2 and WPA2/WPA3 mixed authentication; 802.1X/MAC/Portal authentication"
)
ROAMING = "IEEE 802.11k/v smart roaming and IEEE 802.11r fast roaming"
ROAMING_50 = "IEEE 802.11k/v smart roaming and IEEE 802.11r fast roaming (<= 50 ms)"

URL_162 = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/387e8b1036354d499c727cf377d64fbd/M3T1A590N1046391560142352413/%E5%8D%8E%E4%B8%BA%E5%9D%A4%E7%81%B5%20eKitEngine%20AP162E%E6%97%A0%E7%BA%BF%E6%8E%A5%E5%85%A5%E7%82%B9%E5%BD%A9%E9%A1%B5.pdf"
URL_265 = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/c64c8e9e2e1b4e059ec29f6d31b00751/M3T1A590N1046403185594585348/%E5%8D%8E%E4%B8%BA%E5%9D%A4%E7%81%B5%20eKitEngine%20AP265E%E6%97%A0%E7%BA%BF%E6%8E%A5%E5%85%A5%E7%82%B9%E5%BD%A9%E9%A1%B5.pdf"
URL_266 = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/e54ac3a76f614189835e8e99aa514939/M3T1A590N1051921978522906890/Huawei%20eKitEngine%20AP266%20Wireless%20Access%20Point%20Datasheet.pdf"
URL_271 = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/f94b54ec27244292aa9e7f4fc7a9a1f0/M3T1A590N1124398471928725743/%E5%8D%8E%E4%B8%BA%E5%9D%A4%E7%81%B5%20eKitEngine%20AP271E%E6%97%A0%E7%BA%BF%E6%8E%A5%E5%85%A5%E7%82%B9%E5%BD%A9%E9%A1%B5.pdf"
URL_361 = "https://e.huawei.com/en/documents/products/enterprise-network/4066e75a6d3a470f87517b6eaa8c6102"
URL_362 = "https://ekit.huawei.com/ekit/front/ssr/en/product/-40576"
URL_371 = "https://e.huawei.com/en/documents/products/enterprise-network/6771a6e680a5468b83ffcbbf21ffa97d"
URL_761 = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/d5af8471cd2041e4add8b11e27336eee/M3T1A590N1169748915087012100/Huawei%20eKitEngine%20AP761%20Access%20Point%20Datasheet.pdf"
URL_771 = "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/361bd75eea574df49b3f39c9b364f02b/M3T1A590N1187274761666556192/Huawei%20eKitEngine%20AP771%20Wireless%20Access%20Point%20Datasheet.pdf"


PRODUCTS = {
    "AP162E": {
        "url": URL_162, "title": "Huawei eKitEngine AP162E Wireless Access Point Datasheet", "page": "pp. 2-8",
        "values": {
            "rate_2g_mbps": n(575, "2.4 GHz radio rate: up to 575 Mbps"),
            "rate_5g_mbps": n(2400, "5 GHz radio rate: up to 2.4 Gbps"),
            "max_ssids": n(16, "Maximum number of SSIDs on the device: 16"),
            "fast_roaming": t(ROAMING),
            "wireless_security": t(SECURITY),
        },
    },
    "AP265E": {
        "url": URL_265, "title": "Huawei eKitEngine AP265E Wireless Access Point Datasheet", "page": "feature and radio specification tables",
        "values": {
            "rate_2g_mbps": n(575, "2.4 GHz radio rate: up to 575 Mbps"),
            "rate_5g_mbps": n(2400, "5 GHz radio rate: up to 2.4 Gbps"),
            "max_ssids": n(16, "Maximum number of SSIDs on the device: 16"),
            "fast_roaming": t(ROAMING),
            "wireless_security": t(SECURITY),
        },
    },
    "AP266": {
        "url": URL_266, "title": "Huawei eKitEngine AP266 Wireless Access Point Datasheet", "page": "pp. 2-8",
        "values": {
            "rate_2g_mbps": n(575, "2.4 GHz radio rate: up to 575 Mbps"),
            "rate_5g_mbps": n(2400, "5 GHz radio rate: up to 2.4 Gbps"),
            "max_ssids": n(16, "Maximum quantity of SSIDs: 16"),
            "fast_roaming": t(ROAMING),
            "wireless_security": t(SECURITY),
        },
    },
    "AP271E": {
        "url": URL_271, "title": "Huawei eKitEngine AP271E Wireless Access Point Datasheet", "page": "feature and radio specification tables",
        "values": {
            "rate_2g_mbps": n(690, "2.4 GHz radio rate: up to 0.69 Gbps"),
            "rate_5g_mbps": n(2880, "5 GHz radio rate: up to 2.88 Gbps"),
            "max_ssids": n(10, "Maximum quantity of SSIDs on each radio: <= 10"),
            "wireless_security": t(SECURITY),
        },
    },
    "AP361": {
        "url": URL_361, "title": "Huawei eKitEngine AP361 Access Point Datasheet", "page": "product overview and software feature tables",
        "values": {
            "rate_2g_mbps": n(575, "2.4 GHz: up to 575 Mbps"),
            "rate_5g_mbps": n(1200, "5 GHz: up to 1.2 Gbps"),
            "max_clients": n(128, "Device capacity: <= 128 clients"),
            "fast_roaming": t(ROAMING_50),
        },
    },
    "AP362": {
        "url": URL_362, "title": "Huawei eKitEngine AP362 product specifications and datasheet", "page": "current exact-model product page and software feature table",
        "values": {
            "rate_2g_mbps": n(575, "2.4 GHz: up to 575 Mbps"),
            "rate_5g_mbps": n(2400, "5 GHz: up to 2.4 Gbps"),
            "fast_roaming": t(ROAMING_50),
        },
    },
    "AP371": {
        "url": URL_371, "title": "Huawei eKitEngine AP371 Access Point Datasheet", "page": "product highlights and software feature tables",
        "values": {
            "rate_2g_mbps": n(690, "2.4 GHz: up to 0.69 Gbps"),
            "rate_5g_mbps": n(2880, "5 GHz: up to 2.88 Gbps"),
            "mesh_support": b(True, "Mesh backhaul is supported"),
        },
    },
    "AP761": {
        "url": URL_761, "title": "Huawei eKitEngine AP761 Access Point Datasheet", "page": "pp. 2, 5-11",
        "values": {
            "rate_2g_mbps": n(575, "2.4 GHz: up to 0.575 Gbps"),
            "rate_5g_mbps": n(1200, "5 GHz: up to 1.2 Gbps"),
            "fast_roaming": t(ROAMING_50),
            "wireless_security": t(SECURITY + "; WAPI"),
            "lightning_protection_kv": t("6 kA", "6 kA surge protection for Ethernet ports"),
        },
    },
    "AP771": {
        "url": URL_771, "title": "Huawei eKitEngine AP771 Wireless Access Point Datasheet", "page": "pp. 2-9",
        "values": {
            "rate_2g_mbps": n(690, "2.4 GHz: up to 0.69 Gbps"),
            "rate_5g_mbps": n(2880, "5 GHz: up to 2.88 Gbps"),
            "fast_roaming": t(ROAMING_50),
            "wireless_security": t(SECURITY),
            "mesh_support": b(True, "Mesh backhaul is supported in Fit and cloud/Fat AP modes"),
            "lightning_protection_kv": t("6 kA", "6 kA enhanced surge protection for Ethernet ports"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Huawei eKit AP radio, roaming, security, mesh, SSID, and surge specs (round 2)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="eKit").first()
        if not brand:
            raise CommandError("Missing brand: eKit")
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
                raise CommandError(f"Missing eKit product: {model}")
            document, _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Current official exact-model page/datasheet; accessed 2026-10-23",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": item["title"], "region": "Global",
                    "published_date": None, "accessed_date": accessed, "active": True,
                },
            )
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
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": f"Manually verified from {item['title']}, {item['page']}.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value)); defaults["value_number"] = new_value
                elif kind == "boolean":
                    new_value = bool(value); defaults["value_boolean"] = new_value
                else:
                    new_value = str(value); defaults["value_text"] = new_value
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
                    product_spec=spec, source_document=document,
                    source_location=f"{item['page']} - {model} - {code}",
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
