import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalog.models import Product, ProductSpec, SpecDefinition, SpecEvidence, TemplateField


WALL_INTERFACE_OVERRIDES = {
    "U6-IW": "Uplink/Data-in: 1 x GbE RJ45; Downlink/Data-out: 4 x GbE RJ45",
    "U7-IW": "3 x 2.5GbE RJ45 total: 1 uplink/PoE+ input and 2 downlink; 1 downlink supports PoE output",
    "U7-In-Wall": "3 x 2.5GbE RJ45 total: 1 uplink/PoE+ input and 2 downlink; 1 downlink supports PoE output",
    "UAP-IW": "Uplink/Data-in: 1 x GbE RJ45; Downlink/Data-out: 4 x GbE RJ45",
}


def published(spec):
    return spec and spec.value_status == ProductSpec.ValueStatus.PUBLISHED and bool(spec.value_text.strip())


def power_method_value(*values):
    text = " ; ".join(value for value in values if value)
    lowered = text.casefold()
    parts = []

    standards = set(re.findall(r"802\.3(?:af|at|bt)", text, re.I))
    for first, second in re.findall(r"802\.3(af|at|bt)\s*/\s*(af|at|bt)", text, re.I):
        standards.update((f"802.3{first}", f"802.3{second}"))
    standard_order = {"802.3af": 0, "802.3at": 1, "802.3bt": 2}
    standards = sorted({item.casefold() for item in standards}, key=lambda item: standard_order[item])

    passive_voltage = re.search(r"(\d+(?:\.\d+)?)\s*v\s*(?:dc\s*)?passive\s*poe|passive\s*poe[^;,.]{0,40}?(\d+(?:\.\d+)?)\s*v", text, re.I)
    if "poe" in lowered or standards:
        poe = "PoE"
        if standards:
            poe += f" ({' / '.join(standards)})"
        parts.append(poe)
    if "poe+" in lowered and not standards:
        parts.append("PoE+")
    if passive_voltage:
        voltage = passive_voltage.group(1) or passive_voltage.group(2)
        parts.append(f"Passive PoE ({voltage} V)")
    elif "passive poe" in lowered:
        parts.append("Passive PoE")

    dc_values = []
    for match in re.finditer(r"(?:(\d+(?:\.\d+)?)\s*v\s*dc|dc[^;,.]{0,24}?(\d+(?:\.\d+)?)\s*v)", text, re.I):
        value = match.group(1) or match.group(2)
        if value not in dc_values:
            dc_values.append(value)
    if dc_values:
        parts.append(f"DC ({' / '.join(dc_values)} V)")
    elif re.search(r"\bdc\b", text, re.I):
        parts.append("DC")

    deduped = []
    for part in parts:
        if part not in deduped:
            deduped.append(part)
    return " / ".join(deduped) or re.split(r";|Maximum Power Consumption", text, maxsplit=1, flags=re.I)[0].strip()


def clone_evidence(source, target):
    if not source:
        return
    for evidence in source.evidence.select_related("source_document"):
        SpecEvidence.objects.update_or_create(
            product_spec=target,
            source_document=evidence.source_document,
            source_location=f"Consolidated from {source.definition.code}: {evidence.source_location}"[:250],
            defaults={
                "source_excerpt": evidence.source_excerpt,
                "evidence_level": evidence.evidence_level,
                "verified_by": evidence.verified_by,
                "verified_at": evidence.verified_at,
            },
        )


class Command(BaseCommand):
    help = "Merge AP uplink/networking fields into Ethernet Interfaces and PoE Input into Power Method."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--summary-only", action="store_true")

    def handle(self, *args, **options):
        definitions = {item.code: item for item in SpecDefinition.objects.filter(
            code__in=("ethernet_interfaces", "uplink_interface", "networking_interface", "poe_input", "power_method")
        )}
        ethernet = definitions["ethernet_interfaces"]
        power = definitions["power_method"]
        aps = list(Product.objects.filter(category__slug="access-point").select_related("brand", "product_type"))

        interface_updates = []
        power_updates = []
        for product in aps:
            specs = {
                spec.definition.code: spec
                for spec in product.specs.filter(definition__code__in=definitions).select_related("definition").prefetch_related("evidence")
            }
            current_ethernet = specs.get("ethernet_interfaces")
            networking = specs.get("networking_interface")
            uplink = specs.get("uplink_interface")
            interface_value = WALL_INTERFACE_OVERRIDES.get(product.model)
            if not interface_value and published(networking):
                interface_value = networking.value_text.strip()
            if not interface_value and published(current_ethernet):
                interface_value = current_ethernet.value_text.strip()
            if not interface_value and published(uplink):
                interface_value = f"Uplink: {uplink.value_text.strip()}"
            if interface_value and (
                not published(current_ethernet) or current_ethernet.value_text.strip() != interface_value
            ):
                interface_updates.append((product, interface_value, current_ethernet, networking, uplink))

            poe = specs.get("poe_input")
            current_power = specs.get("power_method")
            if published(poe) or published(current_power):
                power_value = power_method_value(
                    current_power.value_text if published(current_power) else "",
                    poe.value_text if published(poe) else "",
                )
                if power_value and (
                    not published(current_power) or current_power.value_text.strip() != power_value
                ):
                    power_updates.append((product, power_value, current_power, poe))

        self.stdout.write(
            f"Mode: {'apply' if options['apply'] else 'dry-run'}; "
            f"interface updates: {len(interface_updates)}; power updates: {len(power_updates)}"
        )
        if not options["summary_only"]:
            for product, value, *_ in interface_updates:
                self.stdout.write(f"INTERFACE {product.brand.name} {product.model}: {value}")
            for product, value, *_ in power_updates:
                self.stdout.write(f"POWER {product.brand.name} {product.model}: {value}")
        if not options["apply"]:
            return

        today = timezone.localdate()
        with transaction.atomic():
            for product, value, current, networking, uplink in interface_updates:
                source = networking if published(networking) else current if published(current) else uplink
                target, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=ethernet,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": value,
                        "value_number": None,
                        "value_boolean": None,
                        "normalized_value": value,
                        "unit": "",
                        "raw_value": " | ".join(
                            item.raw_value or item.value_text
                            for item in (networking, uplink, current)
                            if published(item)
                        ),
                        "source_url": source.source_url if source else product.official_url,
                        "source_note": "Consolidated Ethernet interface value; wall AP values distinguish uplink/data-in and downlink/data-out.",
                        "verified_date": max(
                            (item.verified_date for item in (networking, uplink, current) if item and item.verified_date),
                            default=today,
                        ),
                    },
                )
                for item in (networking, uplink, current):
                    clone_evidence(item, target)

            for product, value, current, poe in power_updates:
                source = current if published(current) else poe
                target, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=power,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": value,
                        "value_number": None,
                        "value_boolean": None,
                        "normalized_value": value,
                        "unit": "",
                        "raw_value": " | ".join(
                            item.raw_value or item.value_text for item in (current, poe) if published(item)
                        ),
                        "source_url": source.source_url if source else product.official_url,
                        "source_note": "Consolidated AP power-input method. PoE and DC methods are listed in one field.",
                        "verified_date": max(
                            (item.verified_date for item in (current, poe) if item and item.verified_date),
                            default=today,
                        ),
                    },
                )
                for item in (current, poe):
                    clone_evidence(item, target)

            if definitions.get("poe_input"):
                ProductSpec.objects.filter(product__in=aps, definition=definitions["poe_input"]).delete()
            for obsolete_code in ("uplink_interface", "networking_interface"):
                obsolete = definitions.get(obsolete_code)
                if not obsolete:
                    continue
                TemplateField.objects.filter(spec_definition=obsolete).delete()
                ProductSpec.objects.filter(definition=obsolete).delete()
                obsolete.delete()

        self.stdout.write(self.style.SUCCESS(
            f"Applied {len(interface_updates)} interface and {len(power_updates)} power updates; removed obsolete AP interface fields."
        ))
