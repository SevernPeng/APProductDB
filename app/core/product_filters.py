"""Product-catalog filters modelled after the Omada Global catalogue."""

from django.db.models import Q

from catalog.models import ProductSpec
from catalog.nom import has_current_nom


FILTER_PARAMETERS = (
    "nom", "wifi_speed", "wifi_standard", "form_factor", "poe", "port_speed",
    "gateway_type",
)


def _spec_product_ids(codes, query):
    return ProductSpec.objects.filter(
        definition__code__in=codes,
    ).filter(query).values("product_id")


def filter_definitions(family_key):
    fields = []
    if family_key == "wireless":
        fields.extend((
            {
                "name": "wifi_speed", "label": "Wi-Fi Speed",
                "options": tuple((value.lower(), value) for value in (
                    "BE22000", "BE19000", "BE15000", "BE11000", "AX5400", "AX3600",
                    "AX3000", "AX1800", "AC1750", "AC1350", "AC1200", "N300",
                )),
            },
            {
                "name": "wifi_standard", "label": "Wi-Fi Standard",
                "options": (("wifi-7", "Wi-Fi 7"), ("wifi-6", "Wi-Fi 6"),
                            ("wifi-5", "Wi-Fi 5"), ("wifi-4", "Wi-Fi 4")),
            },
            {
                "name": "form_factor", "label": "Form Factor",
                "options": (("ceiling", "Ceiling Mount"), ("outdoor", "Outdoor"),
                            ("wall-plate", "Wall Plate"), ("desktop", "Desktop"),
                            ("bridge", "Wireless Bridge")),
            },
            _port_speed_definition(),
        ))
    elif family_key == "switching":
        fields.extend((_poe_definition(), _port_speed_definition()))
    elif family_key == "gateways":
        fields.extend((
            {
                "name": "gateway_type", "label": "Gateway Type",
                "options": (("wired", "Wired"), ("wifi", "Wi-Fi"),
                            ("cellular", "4G/5G"), ("integrated", "Integrated")),
            },
            {
                "name": "wifi_standard", "label": "Wi-Fi Standard",
                "options": (("wifi-7", "Wi-Fi 7"), ("wifi-6", "Wi-Fi 6"),
                            ("wifi-5", "Wi-Fi 5"), ("wifi-4", "Wi-Fi 4")),
            },
            _poe_definition(),
            _port_speed_definition(),
        ))
    elif family_key == "accessories":
        fields.append(_port_speed_definition())

    fields.append({
        "name": "nom", "label": "NOM Certification",
        "options": (("yes", "With NOM"), ("no", "Without NOM")),
    })
    return fields


def _poe_definition():
    return {
        "name": "poe", "label": "PoE Support",
        "options": (("yes", "PoE"), ("no", "Non-PoE")),
    }


def _port_speed_definition():
    return {
        "name": "port_speed", "label": "Port Speed",
        "options": (("10g", "10 Gbps"), ("2.5g", "2.5 Gbps"),
                    ("1g", "Gigabit"), ("100m", "Fast Ethernet")),
    }


def apply_product_filters(products, values):
    wifi_speed = values.get("wifi_speed", "").upper()
    supported_wifi_speeds = {
        "BE22000", "BE19000", "BE15000", "BE11000", "AX5400", "AX3600",
        "AX3000", "AX1800", "AC1750", "AC1350", "AC1200", "N300",
    }
    if wifi_speed in supported_wifi_speeds:
        products = products.filter(
            Q(product_model__product_name__icontains=wifi_speed)
            | Q(model__icontains=wifi_speed)
        )

    wifi_standard = values.get("wifi_standard")
    wifi_values = {
        "wifi-7": "Wi-Fi 7", "wifi-6": "Wi-Fi 6",
        "wifi-5": "Wi-Fi 5", "wifi-4": "Wi-Fi 4",
    }
    if wifi_standard in wifi_values:
        products = products.filter(wifi_standard__iexact=wifi_values[wifi_standard])

    form_factor = values.get("form_factor")
    form_queries = {
        "ceiling": Q(product_type__code="ceiling") | Q(ap_type="ceiling"),
        "outdoor": Q(product_type__code="outdoor") | Q(ap_type="outdoor"),
        "wall-plate": Q(product_type__code="wall_plate") | Q(ap_type__in=("wall", "wall_plate")),
        "desktop": Q(product_type__code="desktop") | Q(ap_type="desktop"),
        "bridge": Q(category__slug="wireless-bridge"),
    }
    if form_factor in form_queries:
        products = products.filter(form_queries[form_factor])

    gateway_type = values.get("gateway_type")
    gateway_codes = {
        "wired": ("wired_router",), "wifi": ("wireless_router",),
        "cellular": ("cellular_router", "outdoor_cellular_router"),
        "integrated": ("integrated_gateway",),
    }
    if gateway_type in gateway_codes:
        products = products.filter(product_type__code__in=gateway_codes[gateway_type])

    speed = values.get("port_speed")
    speed_queries = {
        "10g": Q(value_number=10) | Q(value_text__icontains="10G"),
        "2.5g": Q(value_number=2.5) | Q(value_text__icontains="2.5"),
        "1g": Q(value_number=1) | Q(value_text__icontains="Gigabit") | Q(value_text__iregex=r"(^|[^0-9])1\s*G"),
        "100m": Q(value_number=0.1) | Q(value_text__icontains="Fast Ethernet") | Q(value_text__icontains="100 Mbps"),
    }
    if speed in speed_queries:
        products = products.filter(pk__in=_spec_product_ids(
            ("ethernet_interfaces", "wan_interfaces", "lan_interfaces",
             "accessory_interface_type", "accessory_data_rate_gbps"),
            speed_queries[speed],
        ))

    poe_spec_ids = _spec_product_ids(
        ("poe_ports", "router_poe_ports", "poe_budget_w", "router_poe_budget_w"),
        Q(value_number__gt=0),
    )
    poe_text_ids = _spec_product_ids(
        ("poe_standard", "poe_input", "poe_output", "accessory_poe_standard"),
        ~Q(value_text="") & ~Q(value_text__iexact="No") & ~Q(value_text__iexact="N/A"),
    )
    poe_query = (
        Q(product_type__code__in=(
            "campus_poe", "l2_poe", "l3_poe", "agile_poe", "industrial_poe",
            "unmanaged_poe", "easy_smart_poe", "poe_injector",
        ))
        | Q(pk__in=poe_spec_ids)
        | Q(pk__in=poe_text_ids)
    )
    if values.get("poe") == "yes":
        products = products.filter(poe_query)
    elif values.get("poe") == "no":
        products = products.exclude(poe_query)

    nom = values.get("nom")
    if nom in {"yes", "no"}:
        nom_ids = [pk for pk, records in products.values_list("pk", "nom_records")
                   if has_current_nom(records or [])]
        products = products.filter(pk__in=nom_ids) if nom == "yes" else products.exclude(pk__in=nom_ids)
    return products
