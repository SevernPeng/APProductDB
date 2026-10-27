"""Resolve comparison values from standard fields and imported workbook rows.

Workbook codes contain a sheet name and row number, not a shared field ID.
Match explicit equivalent labels instead; never borrow another product's data.
"""
import re
from dataclasses import dataclass
from decimal import Decimal

from catalog.spec_applicability import has_published_value


ALIASES = {
    "ethernet_interfaces": ("Interface",),
    "supported_bands": ("Frequency",),
    "antenna_type": ("Antenna",),
    "max_clients": ("Concurrent Clients", "Client Capacity"),
    "power_method": ("Power Supply",),
    "max_power_consumption_w": ("Max. Power Consumption", "Max Power Consumption"),
    "packet_buffer_mb": ("Packet Buffer Memory",),
    "l2_features": ("L2 Features", "L2 and L2+ Features"),
    "l3_features": ("L3 Features", "Advanced Routing", "Routing"),
    "vlan_count": ("Maximum VLANs",),
    "management_methods": ("Management Features", "Centralized Management"),
    "controller_management": ("Centralized Management", "Management", "Cloud Management"),
    "installation": ("Mounting", "Installation"),
    "mounting_options": ("Mounting", "Installation"),
    "fan_design": ("Fan Quantity", "Fan"),
    "poe_configuration": ("PoE Port Configuration", "PoE Port"),
    "poe_standard": ("PoE Standard",),
    "poe_budget_w": ("Total PoE Budget", "PoE Budget"),
    "router_poe_budget_w": ("PoE Budget",),
    "max_poe_per_port_w": ("Max. PoE Output per Port", "Max PoE Output per Port"),
    "acl_security": ("Security", "Access Control List", "ACL"),
    "qos_support": ("QoS", "Quality of Service"),
    "vlan_support": ("VLAN",),
    "stacking_units": ("Stacking Number",),
    "stacking_bandwidth_gbps": ("Stack Bandwidth", "Stancking Bandwitch"),
    "ip_rating": ("Weatherproof Enclosure",),
    "lightning_protection_kv": ("Surge Protection", "Lightning Protection"),
    "wireless_range": ("Transmission Distance",),
    "coverage_area_m2": ("Coverage",),
    "nat_throughput_mbps": ("NAT Throughput (Static IP)", "NAT (Static IP)"),
    "vpn_throughput_mbps": ("IPsec VPN Throughput", "VPN Throughput"),
    "sd_wan": ("SD-WAN",),
    "wan_load_balancing": ("Multi-WAN Failover & Load Balancing", "Multi-WAN"),
    "firewall_features": ("Firewall", "Security", "Attack Defense", "Access Control"),
    "sim_interfaces": ("SIM Slot",),
    "cpu": ("Processor",),
    "enclosure_material": ("Enclosure", "Material"),
    "cable_test": ("Cable Diagnostics",),
}

# Extract only explicitly labelled lines; absence is not evidence of "No".
LINE_FIELDS = {
    "lan_interfaces": ("ethernet_interfaces", r"\bLAN\b"),
    "wan_interfaces": ("ethernet_interfaces", r"\bWAN\b"),
    "uplink_interfaces": ("ethernet_interfaces", r"\bSFP\+?|\buplink\b"),
    "usb_interfaces": ("ethernet_interfaces", r"\bUSB(?:-C)?\b"),
    "switch_usb_interfaces": ("ethernet_interfaces", r"\bUSB(?:-C)?\b"),
    "console_interfaces": ("ethernet_interfaces", r"\bconsole\b"),
    "ip_interface_capacity": ("l2_features", r"\d+\s+IP\s+Interfaces?\b"),
    "dhcp_features": ("l2_features", r"\bDHCP\b"),
    "stp_features": ("l2_features", r"\b(?:Spanning Tree|MSTP|RSTP|STP)\b"),
    "routing_entry_capacity": ("l2_features", r"\d+.*\b(?:Static Routes?|Routing Entries)\b"),
    "arp_entry_capacity": ("l2_features", r"\d+.*\bARP\s+entries\b"),
    "vlan_count": ("vlan_support", r"\d+\s*K?\s+VLAN\s+Groups?\b"),
    "l3_features": ("l2_features", r"\b(?:Static Routes?|Routing|Proxy ARP|DHCP (?:Server|Relay))\b"),
}


def label_key(label):
    return re.sub(r"\s+", " ", label.strip()).casefold()


@dataclass(frozen=True)
class ComparisonValue:
    display_value: str
    effective_source_url: str


class SpecResolver:
    def __init__(self, product, definitions):
        self.product = product
        self.specs = {s.definition.code: s for s in product.specs.all()}
        self.matrix = [s for s in self.specs.values()
                       if s.definition.active and s.definition.code.startswith("matrix-")]
        self.by_label = {}
        for spec in self.matrix:
            self.by_label.setdefault(label_key(spec.definition.display_name), []).append(spec)
        self.labels = {
            d.code: (d.display_name, *ALIASES.get(d.code, ())) for d in definitions
        }
        self.consumed = set()

    def wireless_bands(self):
        spec = self.resolve("supported_bands")
        if spec and spec.display_value not in {"Unknown", "Not Published", "Not Applicable"}:
            return {band for band in ("2.4", "5", "6")
                    if re.search(rf"(?<![\d.]){re.escape(band)}(?![\d.])", spec.display_value)}
        return set()

    def wireless_value(self, code):
        band_codes = {"2.4": "2g", "5": "5g", "6": "6g"}
        if code.startswith("rate_"):
            band = next((b for b, suffix in band_codes.items() if code == f"rate_{suffix}_mbps"), None)
            if band:
                for spec in self.by_label.get("signal rate", []):
                    if not has_published_value(spec):
                        continue
                    match = re.search(
                        rf"(?<![\d.]){re.escape(band)}\s*GHz\s*:\s*([\d,]+(?:\.\d+)?)\s*(Mbps|Gbps)",
                        spec.display_value, re.I,
                    )
                    if match:
                        rate = Decimal(match[1].replace(",", ""))
                        if match[2].casefold() == "gbps":
                            rate *= 1000
                        number = format(rate, "f")
                        if "." in number:
                            number = number.rstrip("0").rstrip(".")
                        return ComparisonValue(f"{number} Mbps", spec.effective_source_url)
        if code == "total_spatial_streams":
            bands = self.wireless_bands()
            if not bands:
                return None
            antenna = self.antenna()
            total = 0
            sources = set()
            for band in bands:
                mimo = self.specs.get(f"mimo_{band_codes[band]}")
                match = re.search(r"(\d+)\s*[x×]\s*(\d+)(?:\s*:\s*(\d+))?", mimo.display_value) if has_published_value(mimo) else None
                if match:
                    total += int(match[3]) if match[3] else min(int(match[1]), int(match[2]))
                    sources.add(mimo.effective_source_url)
                    continue
                match = re.search(rf"{re.escape(band)}\s*GHz\s*:\s*(\d+)\s*[x×]", antenna.display_value, re.I)
                if not match:
                    return None
                total += int(match[1])
                sources.add(antenna.effective_source_url)
            return ComparisonValue(str(total), sources.pop() if len(sources) == 1 else "")
        return None

    def aggregate_rate(self):
        bands = self.wireless_bands()
        if not bands:
            return ComparisonValue("Unknown", "")
        total = Decimal("0")
        sources = set()
        for band, suffix in (("2.4", "2g"), ("5", "5g"), ("6", "6g")):
            if band not in bands:
                continue
            value = self.resolve(f"rate_{suffix}_mbps")
            match = re.fullmatch(r"([\d,]+(?:\.\d+)?)\s*(Mbps|Gbps)", value.display_value, re.I) if value else None
            if not match:
                return ComparisonValue("Unknown", "")
            total += Decimal(match[1].replace(",", "")) * (1000 if match[2].casefold() == "gbps" else 1)
            sources.add(value.effective_source_url)
        number = format(total, "f")
        if "." in number:
            number = number.rstrip("0").rstrip(".")
        return ComparisonValue(f"{number} Mbps", sources.pop() if len(sources) == 1 else "")

    def antenna(self):
        matrix = self.by_label.get("antenna", [])
        self.consumed.update(spec.pk for spec in matrix)
        candidates = [spec for spec in matrix if has_published_value(spec)]
        if not candidates:
            candidates = [self.specs.get(code) for code in ("antenna_type", "antenna_gain_dbi")]
            candidates = [spec for spec in candidates if has_published_value(spec)]
        if not candidates:
            spec = self.specs.get("antenna_type") or self.specs.get("antenna_gain_dbi")
            return ComparisonValue(spec.display_value if spec else "Unknown",
                                   spec.effective_source_url if spec else "")
        bands = {}
        for spec in candidates:
            for match in re.finditer(
                r"(2\.4|5|6)\s*GHz\s*:\s*[•·]?\s*(\d+)\s*[x×]\s*(\d+(?:\.\d+)?)\s*dBi",
                spec.display_value, re.I,
            ):
                band, count, gain = match.groups()
                gain = gain if "." in gain else f"{gain}.0"
                bands.setdefault(band, f"• {band} GHz: {count}× {gain} dBi")
        text = "\n".join(bands[band] for band in ("2.4", "5", "6") if band in bands)
        if not text:
            text = "\n".join(dict.fromkeys(line.strip() for spec in candidates
                for line in spec.display_value.splitlines() if line.strip()))
        urls = {spec.effective_source_url for spec in candidates}
        return ComparisonValue(text, urls.pop() if len(urls) == 1 else "")

    def resolve(self, code):
        direct = self.specs.get(code)
        if code in {"mesh_support", "fast_roaming"}:
            value = self.wireless_function(code)
            if value:
                return value
        candidates = []
        for label in self.labels.get(code, ALIASES.get(code, ())):
            candidates.extend(self.by_label.get(label_key(label), []))
        if has_published_value(direct):
            self.consumed.update(s.pk for s in candidates)
            return direct
        # Preserve explicit not-applicable states; unknown placeholders may fall back.
        if direct and direct.value_status == "not_applicable":
            return direct
        published = [s for s in candidates if has_published_value(s)]
        if published:
            self.consumed.update(s.pk for s in published)
            # Keep complete source text, including units and qualifiers. Do not
            # reduce bidirectional or per-protocol throughput to the first number.
            values = list(dict.fromkeys(s.display_value for s in published))
            urls = {s.effective_source_url for s in published}
            return ComparisonValue("\n".join(values), urls.pop() if len(urls) == 1 else "")
        if code == "total_spatial_streams" or code in {"rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps"}:
            value = self.wireless_value(code)
            if value:
                return value
        if code in LINE_FIELDS:
            parent_code, pattern = LINE_FIELDS[code]
            parent = self.resolve(parent_code)
            if parent:
                lines = [line.strip() for line in parent.display_value.splitlines()
                         if re.search(pattern, line, re.I)]
                if lines:
                    return ComparisonValue("\n".join(lines), parent.effective_source_url)
        return direct

    def wireless_function(self, code):
        for spec in self.by_label.get("wireless functions", []):
            if not has_published_value(spec):
                continue
            for line in re.split(r"[\r\n•;]+", spec.display_value):
                if code == "mesh_support":
                    feature = re.search(r"\bmesh\b", line, re.I)
                else:
                    feature = next((match for match in re.finditer(
                        r"802\.11\s*([kvr](?:\s*[/,]\s*[kvr])*)\b", line, re.I
                    ) if "r" in match[1].casefold()), None)
                if not feature:
                    continue
                before = line[:feature.start()]
                after = line[feature.end():]
                negative = bool(
                    re.search(r"\b(?:no|without|not supported|does not support)\s*$", before, re.I)
                    or re.match(r"\s*[:=-]?\s*(?:not supported|unsupported|disabled|no|false)\b", after, re.I)
                )
                return ComparisonValue(
                    "No" if negative else "Yes" if code == "mesh_support" else "802.11r",
                    spec.effective_source_url,
                )
        # A collected k/v value alone is not proof of fast transition support.
        direct = self.specs.get(code)
        if code == "fast_roaming" and has_published_value(direct):
            protocols = list(re.finditer(r"802\.11\s*([kvr](?:\s*[/,]\s*[kvr])*)\b",
                                         direct.display_value, re.I))
            if protocols and not any("r" in match[1].casefold() for match in protocols):
                return ComparisonValue("Unknown", direct.effective_source_url)
        return None

    def workbook_poe_state(self):
        unsupported = False
        for label in ("Total PoE Budget", "PoE Budget", "PoE Port Configuration", "PoE Port"):
            for spec in self.by_label.get(label_key(label), []):
                if not has_published_value(spec):
                    continue
                text = spec.display_value.strip().casefold()
                if text in {"no", "false", "none"} or re.fullmatch(r"0(?:\.0+)?\s*(?:w|ports?)?", text):
                    unsupported = True
                elif not re.search(r"non[- ]poe|no poe|without poe", text):
                    return True
                else:
                    unsupported = True
        return False if unsupported else None
