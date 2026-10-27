import re
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Product, ProductSpec, SpecDefinition
from catalog.spec_applicability import has_published_value, specs_by_code


def _round_decimal(value, places=3):
    return Decimal(str(round(value, places))).quantize(Decimal("0.001"))


class Command(BaseCommand):
    help = "Populate deterministic derived specifications from verified product data and model conventions."

    def add_arguments(self, parser):
        parser.add_argument("--brand", action="append", dest="brands")
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        products = Product.objects.filter(is_published=True).select_related(
            "brand", "category", "product_type", "product_model"
        ).prefetch_related("specs__definition")
        if options["brands"]:
            products = products.filter(brand__name__in=options["brands"])

        definitions = {
            item.code: item for item in SpecDefinition.objects.filter(active=True)
        }
        created = 0

        def set_value(
            product, current, code, kind, value, reason, source_url="", force=False
        ):
            nonlocal created
            if code not in definitions or (
                has_published_value(current.get(code)) and not force
            ):
                return
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "",
                "value_number": None,
                "value_boolean": None,
                "normalized_value": str(value),
                "unit": definitions[code].unit,
                "raw_value": reason[:1000],
                "source_url": (source_url or product.official_url)[:200],
                "source_note": f"Deterministically derived: {reason}"[:1000],
                "verified_date": date.today(),
            }
            if kind == "text":
                defaults["value_text"] = str(value)
            elif kind == "number":
                defaults["value_number"] = _round_decimal(float(value))
            else:
                defaults["value_boolean"] = bool(value)
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definitions[code],
                defaults=defaults,
            )
            current[code] = spec
            created += 1

        for product in products:
            current = specs_by_code(product)
            category = product.category.slug
            model = product.model.upper()

            if category == "access-point":
                standard = (product.wifi_standard or "").casefold()
                if "wi-fi 7" in standard or "wifi 7" in standard or "802.11be" in standard:
                    set_value(product, current, "supported_bands", "text", "2.4 GHz / 5 GHz / 6 GHz", "Wi-Fi 7 radio-band rule")
                    set_value(product, current, "max_channel_width_mhz", "number", 320, "Wi-Fi 7 maximum channel-width rule")
                elif "wi-fi 6e" in standard or "wifi 6e" in standard:
                    set_value(product, current, "supported_bands", "text", "2.4 GHz / 5 GHz / 6 GHz", "Wi-Fi 6E radio-band rule")
                    set_value(product, current, "max_channel_width_mhz", "number", 160, "Wi-Fi 6E maximum channel-width rule")
                elif standard:
                    set_value(product, current, "supported_bands", "text", "2.4 GHz / 5 GHz", f"{product.wifi_standard} radio-band rule")
                    rate_5g = current.get("rate_5g_mbps")
                    rate = float(rate_5g.value_number) if has_published_value(rate_5g) and rate_5g.value_number is not None else 0
                    width = 160 if "wi-fi 6" in standard and rate > 1800 else 80
                    set_value(product, current, "max_channel_width_mhz", "number", width, f"{product.wifi_standard} and 5 GHz rate rule")
                if not has_published_value(current.get("supported_bands")):
                    bands = []
                    if has_published_value(current.get("rate_2g_mbps")):
                        bands.append("2.4 GHz")
                    if has_published_value(current.get("rate_5g_mbps")):
                        bands.append("5 GHz")
                    if has_published_value(current.get("rate_6g_mbps")):
                        bands.append("6 GHz")
                    if not bands:
                        # Enterprise AP records are dual-band unless the official
                        # standard/radio table proves a different configuration.
                        bands = ["2.4 GHz", "5 GHz"]
                    set_value(
                        product, current, "supported_bands", "text", " / ".join(bands),
                        "radio bands from published per-band rates; otherwise enterprise AP dual-band baseline",
                    )
                if not has_published_value(current.get("total_spatial_streams")):
                    inferred_streams = 0
                    complete = True
                    width_spec = current.get("max_channel_width_mhz")
                    width = float(width_spec.value_number) if has_published_value(width_spec) and width_spec.value_number is not None else 0
                    for code in ("rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps"):
                        rate_spec = current.get(code)
                        if not has_published_value(rate_spec) or rate_spec.value_number is None:
                            continue
                        rate = float(rate_spec.value_number)
                        if code == "rate_2g_mbps":
                            streams = 4 if rate >= 1000 else 2 if rate >= 250 else 1
                        elif rate >= 4500:
                            streams = 4
                        elif rate >= 1800:
                            streams = 2 if width >= 160 else 4
                        elif rate >= 1000:
                            streams = 2
                        elif rate >= 700:
                            streams = 2
                        elif rate >= 400:
                            streams = 1
                        else:
                            streams = max(1, round(rate / 150))
                        inferred_streams += streams
                    if complete and inferred_streams:
                        set_value(product, current, "total_spatial_streams", "number", inferred_streams, "sum of deterministic stream counts from published per-band rates and channel width")

            if category in {"managed-switches", "unmanaged-easy-smart-switches"}:
                capacity = current.get("switching_capacity_gbps")
                forwarding = current.get("packet_forwarding_rate_mpps")
                if not has_published_value(capacity) and has_published_value(forwarding) and forwarding.value_number is not None:
                    derived = round(float(forwarding.value_number) / 0.744)
                    set_value(product, current, "switching_capacity_gbps", "number", derived, "line-rate capacity from packet forwarding rate ÷ 0.744", forwarding.source_url)
                elif has_published_value(capacity) and capacity.value_number is not None and not has_published_value(forwarding):
                    derived = round(float(capacity.value_number) * 0.744, 2)
                    set_value(product, current, "packet_forwarding_rate_mpps", "number", derived, "64-byte line-rate forwarding from switching capacity × 0.744", capacity.source_url)
                interface_spec = current.get("ethernet_interfaces")
                replace_generic_interface = bool(
                    has_published_value(interface_spec)
                    and (interface_spec.source_note or "").startswith(
                        "Deterministically derived:"
                    )
                    and "exact port mix" in (interface_spec.value_text or "")
                )
                normalized = re.sub(r"[^A-Z0-9-]", "", model)
                number_match = re.search(
                    r"(?:TL-(?:SF|SG|SX)|(?:LS|SG|DS))(\d{3,4})",
                    normalized,
                )
                port_count = int(number_match.group(1)[-2:]) if number_match else 0
                speed = 0
                speed_label = ""
                if normalized.startswith("TL-SX"):
                    speed, speed_label = 10, "10G"
                elif "-M2" in normalized:
                    speed, speed_label = 2.5, "2.5G"
                elif normalized.startswith(("TL-SG", "SG", "DS")) or "G" in normalized[:8]:
                    speed, speed_label = 1, "Gigabit"
                elif normalized.startswith(("TL-SF", "LS")) and "G" not in normalized:
                    speed, speed_label = 0.1, "10/100 Mbps"
                if not has_published_value(interface_spec) or replace_generic_interface:
                    if 2 <= port_count <= 64 and speed:
                        set_value(
                            product, current, "ethernet_interfaces", "text",
                            f"{port_count} x {speed_label} Ethernet ports",
                            "port count and nominal port speed encoded in TP-Link switch model",
                            force=replace_generic_interface,
                        )
                if 2 <= port_count <= 64 and speed:
                    set_value(product, current, "switching_capacity_gbps", "number", port_count * speed * 2, "full-duplex line-rate capacity from model-encoded port count and speed")
                    set_value(product, current, "packet_forwarding_rate_mpps", "number", port_count * speed * 2 * 0.744, "64-byte line-rate forwarding from model-encoded ports")
                if not has_published_value(current.get("ethernet_interfaces")):
                    set_value(
                        product, current, "ethernet_interfaces", "text",
                        "Ethernet switching interfaces (exact port mix not published in retained source)",
                        "product is classified by the manufacturer as an Ethernet switch; exact port mix remains an optional detail",
                    )
                if (
                    product.brand.name == "TP-Link"
                    and product.product_type_id
                    and product.product_type.code == "easy_smart"
                ):
                    set_value(product, current, "igmp_snooping", "text", "IGMP Snooping", "TP-Link Easy Smart feature baseline")
                if product.product_type_id and product.product_type.code in {
                    "unmanaged", "easy_smart"
                }:
                    management_type = (
                        "Unmanaged"
                        if product.product_type.code == "unmanaged"
                        else "Easy Smart"
                    )
                    set_value(
                        product, current, "management_type", "text", management_type,
                        "manufacturer product taxonomy classifies the switch management type",
                        force=True,
                    )

            if category == "gateway" and not has_published_value(current.get("ethernet_interfaces")):
                set_value(
                    product, current, "ethernet_interfaces", "text",
                    "Ethernet WAN/LAN interfaces (exact port mix not published in retained source)",
                    "gateway/router product classification confirms Ethernet WAN/LAN connectivity; exact port mix remains optional",
                )

            if category == "wireless-bridge" and not has_published_value(current.get("supported_bands")):
                if re.search(r"(?:^|[-_])2(?:G|NT|N)(?:[-_/]|$)", model):
                    bridge_bands = "2.4 GHz"
                elif "MLO6" in model or "BRIDGE 7" in model:
                    bridge_bands = "5 GHz / 6 GHz"
                else:
                    bridge_bands = "5 GHz"
                set_value(
                    product, current, "supported_bands", "text", bridge_bands,
                    "dedicated wireless-bridge band family encoded in the official model name",
                )

            if category != "accessories" or not product.product_type_id:
                continue
            product_type = product.product_type.code

            if product_type == "power_supply":
                watts_match = re.search(r"(?:PWR-|APS)(\d{3,4})W?", model)
                if watts_match:
                    set_value(
                        product, current, "accessory_power_w", "number",
                        int(watts_match.group(1)),
                        "rated output power encoded in the official power-supply model",
                    )

            if product_type in {"optical_module", "dac_cable"}:
                if "100G" in model or "QSFP" in model or model.startswith(("SM9", "E100G")):
                    interface, rate = "QSFP28", 100
                elif "25G" in model or "SFP28" in model or model.startswith(("SM6", "E25G")):
                    interface, rate = "SFP28", 25
                elif "10G" in model or "SFPP" in model or model.startswith(("SM5", "SM52", "10G-")):
                    interface, rate = "SFP+", 10
                else:
                    interface, rate = "SFP", 1.25
                set_value(product, current, "accessory_interface_type", "text", interface, "standard transceiver family encoded in model")
                set_value(product, current, "accessory_data_rate_gbps", "number", rate, "standard transceiver family encoded in model")

            if product_type in {"optical_module", "dac_cable", "media_converter", "poe_injector"}:
                fallback_interfaces = {
                    "optical_module": "Pluggable optical/copper transceiver",
                    "dac_cable": "Direct-attach transceiver cable",
                    "media_converter": "Ethernet / fiber media-converter interfaces",
                    "poe_injector": "2 x RJ45 Ethernet ports",
                }
                set_value(
                    product, current, "accessory_interface_type", "text",
                    fallback_interfaces[product_type],
                    "manufacturer product type establishes the interface family; exact connector or speed remains optional",
                )

            if product_type == "optical_module":
                is_copper = bool(re.search(r"(?:^|[-_])(?:T|TE|RJ45)(?:$|[-_])", model)) or model.endswith(("331T", "5310-T"))
                set_value(product, current, "accessory_connector_type", "text", "RJ45" if is_copper else "LC", "connector family encoded in optical-module model")
                if not is_copper:
                    if re.search(r"(?:SR|SX|LM|MM)", model):
                        set_value(product, current, "accessory_fiber_mode", "text", "Multi-mode", "SR/SX/LM/MM optical model convention")
                    elif re.search(r"(?:LR|LX|LS|SM|BX|BXD|BXU)", model):
                        set_value(product, current, "accessory_fiber_mode", "text", "Single-mode", "LR/LX/LS/SM/BX optical model convention")
                    distance_match = re.search(r"-(\d{1,3})(?:KM)?(?:-|$)", model)
                    if distance_match:
                        set_value(product, current, "accessory_max_distance_km", "number", int(distance_match.group(1)), "transmission distance encoded in model suffix")
                    elif re.search(r"(?:LR|LS|LX)", model):
                        set_value(product, current, "accessory_max_distance_km", "number", 10, "standard LR/LS/LX reach convention")
                    elif re.search(r"(?:SR|SX)", model):
                        set_value(product, current, "accessory_max_distance_km", "number", 0.3, "standard SR/SX reach convention")
                    elif "LM" in model:
                        set_value(product, current, "accessory_max_distance_km", "number", 0.55, "TP-Link LM multimode reach convention")

            if product_type == "dac_cable":
                length_match = re.search(r"(?:-|_)(\d+(?:\.\d+)?)M$", model)
                if length_match:
                    set_value(product, current, "accessory_cable_length_m", "number", float(length_match.group(1)), "cable length encoded in model suffix")

            if product_type == "poe_injector":
                set_value(product, current, "accessory_interface_type", "text", "2× RJ45 Ethernet ports", "PoE injector topology")
                poe_rules = (
                    (("380",), "802.3af / 802.3at / 802.3bt", 90),
                    (("170", "370", "5460"), "802.3af / 802.3at / 802.3bt", 60),
                    (("160", "260"), "802.3af / 802.3at", 30),
                    (("150",), "802.3af", 15.4),
                )
                for markers, standard, watts in poe_rules:
                    if any(marker in model for marker in markers):
                        set_value(product, current, "accessory_poe_standard", "text", standard, "TP-Link PoE injector model family")
                        set_value(product, current, "accessory_power_w", "number", watts, "TP-Link PoE injector model family")
                        break

            if product_type == "mounting":
                if model == "APM-200":
                    mounting = "Pole or wall mounting; 150° adjustable"
                elif model == "APM-103":
                    mounting = "Adjustable outdoor AP mounting bracket (±45° vertical/horizontal)"
                else:
                    mounting = "Magnetic mounting" if "MAG" in model else "Rack mounting"
                set_value(product, current, "accessory_mounting_type", "text", mounting, "mounting type encoded in product model")

            if product_type == "media_converter":
                set_value(product, current, "accessory_interface_type", "text", "Ethernet / fiber media converter", "media-converter product type")
                if model.startswith(("MC1", "DMC-1")):
                    set_value(product, current, "accessory_data_rate_gbps", "number", 0.1, "100 Mbps media-converter model family")
                else:
                    set_value(product, current, "accessory_data_rate_gbps", "number", 1, "Gigabit media-converter model family")
                if model == "MC220L":
                    set_value(product, current, "accessory_connector_type", "text", "SFP", "MC220L official interface design")
                else:
                    set_value(product, current, "accessory_connector_type", "text", "SC", "TP-Link MC-series fiber connector")
                if model.endswith("CM"):
                    set_value(product, current, "accessory_fiber_mode", "text", "Multi-mode", "CM media-converter model family")
                elif model.endswith("CS"):
                    set_value(product, current, "accessory_fiber_mode", "text", "Single-mode", "CS media-converter model family")
                media_distance = {
                    "MC100CM": 2,
                    "MC110CS": 20,
                    "MC200CM": 0.55,
                    "MC210CS": 20,
                }.get(model)
                if media_distance is not None:
                    set_value(product, current, "accessory_max_distance_km", "number", media_distance, "TP-Link official MC-series product matrix")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "DERIVED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: products={products.count()} specs_created={created}"))
