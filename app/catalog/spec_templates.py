"""Canonical specification definitions and comparison templates by product type."""


def spec(name, group, data_type="text", unit="", *, filterable=False, direction="none", category=None, description=""):
    return {
        "display_name": name,
        "group": group,
        "data_type": data_type,
        "unit": unit,
        "is_filterable": filterable,
        "comparison_direction": direction,
        "category_slug": category,
        "description": description or name,
    }


SPEC_DEFINITIONS = {
    # Wireless performance and radio design
    "supported_bands": spec("Supported Wireless Bands", "Wireless", filterable=True, category="access-point"),
    "total_spatial_streams": spec("Total Spatial Streams", "Wireless", "integer", filterable=True, direction="higher", category="access-point"),
    "mimo_2g": spec("2.4 GHz MIMO", "Wireless", category="access-point"),
    "mimo_5g": spec("5 GHz MIMO", "Wireless", category="access-point"),
    "mimo_6g": spec("6 GHz MIMO", "Wireless", category="access-point"),
    "rate_2g_mbps": spec("2.4 GHz Max Rate", "Performance", "integer", "Mbps", filterable=True, direction="higher", category="access-point"),
    "rate_5g_mbps": spec("5 GHz Max Rate", "Performance", "integer", "Mbps", filterable=True, direction="higher", category="access-point"),
    "rate_6g_mbps": spec("6 GHz Max Rate", "Performance", "integer", "Mbps", filterable=True, direction="higher", category="access-point"),
    "max_channel_width_mhz": spec("Max Channel Width", "Wireless", "integer", "MHz", filterable=True, direction="higher", category="access-point"),
    "antenna_type": spec("Antenna Type", "Wireless", category="access-point"),
    "antenna_gain_dbi": spec("Antenna Gain", "Wireless", unit="dBi", direction="higher", category="access-point"),
    "beamwidth": spec("Antenna Beamwidth", "Wireless", category="wireless-bridge"),
    "wireless_range": spec("Coverage / Transmission Distance", "Coverage", direction="higher", category="wireless-bridge"),
    "max_clients": spec("Maximum Clients", "Capacity", "integer", filterable=True, direction="higher", category="access-point"),
    "max_ssids": spec("Maximum SSIDs", "Capacity", "integer", direction="higher", category="access-point"),
    "bridge_modes": spec("Bridge / Operating Modes", "Wireless", category="wireless-bridge"),
    "max_bridge_pairs": spec("Maximum Bridge Links", "Capacity", "integer", direction="higher", category="wireless-bridge"),
    # Interfaces and power
    "ethernet_interfaces": spec("Ethernet Interfaces", "Interfaces", filterable=True),
    "wan_interfaces": spec("WAN Interfaces", "Interfaces", category="gateway"),
    "lan_interfaces": spec("LAN Interfaces", "Interfaces", category="gateway"),
    "uplink_interfaces": spec("Uplink / SFP Interfaces", "Interfaces", category="managed-switches"),
    "usb_interfaces": spec("USB Interfaces", "Interfaces", category="gateway"),
    "poe_input": spec("PoE Input", "Power", category="access-point"),
    "poe_output": spec("PoE Output", "Power", category="access-point"),
    "poe_standard": spec("Supported PoE Standards", "PoE", filterable=True, category="managed-switches"),
    "poe_ports": spec("PoE-Capable Ports", "PoE", "integer", direction="higher", category="managed-switches"),
    "poe_budget_w": spec("Total PoE Budget", "PoE", "decimal", "W", filterable=True, direction="higher", category="managed-switches"),
    "max_poe_per_port_w": spec("Maximum PoE per Port", "PoE", "decimal", "W", direction="higher", category="managed-switches"),
    "max_power_consumption_w": spec("Maximum Power Consumption", "Power", "decimal", "W", direction="lower"),
    "redundant_power": spec("Redundant Power Supply", "Power", "boolean", category="managed-switches"),
    # AP features
    "centralized_management": spec("Centralized Management", "Management", category="access-point"),
    "mesh_support": spec("Mesh Support", "Management", "boolean", category="access-point"),
    "fast_roaming": spec("Fast Roaming", "Management", category="access-point"),
    "wireless_security": spec("Wireless Security", "Security", category="access-point"),
    # Gateway performance and features
    "routing_throughput_mbps": spec("Routing Throughput", "Performance", "decimal", "Mbps", direction="higher", category="gateway"),
    "nat_throughput_mbps": spec("NAT Throughput", "Performance", "decimal", "Mbps", direction="higher", category="gateway"),
    "vpn_throughput_mbps": spec("VPN / IPsec Throughput", "Performance", "decimal", "Mbps", filterable=True, direction="higher", category="gateway"),
    "concurrent_sessions": spec("Concurrent Sessions", "Capacity", "integer", filterable=True, direction="higher", category="gateway"),
    "vpn_tunnels": spec("VPN Tunnels", "Capacity", "integer", direction="higher", category="gateway"),
    "wan_load_balancing": spec("Multi-WAN Load Balancing", "Routing", "boolean", category="gateway"),
    "sd_wan": spec("SD-WAN Capabilities", "Routing", category="gateway"),
    "firewall_features": spec("Firewall / Security Features", "Security", category="gateway"),
    "vpn_protocols": spec("Supported VPN Protocols", "Security", category="gateway"),
    "controller_management": spec("Controller / Cloud Management", "Management", category="gateway"),
    "router_wifi_standard": spec("Wi-Fi Standard", "Wireless", category="gateway"),
    "router_supported_bands": spec("Supported Wireless Bands", "Wireless", category="gateway"),
    "router_wireless_rate_mbps": spec("Maximum Wireless Rate", "Wireless", "decimal", "Mbps", direction="higher", category="gateway"),
    "cellular_standard": spec("Cellular Standard", "Cellular", category="gateway"),
    "sim_interfaces": spec("SIM Interfaces", "Cellular", category="gateway"),
    "cellular_downlink_mbps": spec("Cellular Downlink Rate", "Cellular", "decimal", "Mbps", direction="higher", category="gateway"),
    "router_poe_ports": spec("PoE-Capable LAN Ports", "PoE", "integer", direction="higher", category="gateway"),
    "router_poe_budget_w": spec("Router PoE Budget", "PoE", "decimal", "W", direction="higher", category="gateway"),
    # Switch performance and features
    "switching_capacity_gbps": spec("Switching Capacity", "Performance", "decimal", "Gbps", filterable=True, direction="higher", category="managed-switches"),
    "packet_forwarding_rate_mpps": spec("Packet Forwarding Rate", "Performance", "decimal", "Mpps", direction="higher", category="managed-switches"),
    "mac_address_table": spec("MAC Address Table", "Capacity", direction="higher", category="managed-switches"),
    "packet_buffer_mb": spec("Packet Buffer", "Capacity", "decimal", "MB", direction="higher", category="managed-switches"),
    "jumbo_frame_bytes": spec("Jumbo Frame", "Capacity", "integer", "bytes", direction="higher", category="managed-switches"),
    "vlan_count": spec("Maximum VLANs", "Capacity", "integer", direction="higher", category="managed-switches"),
    "l2_features": spec("Layer 2 Features", "Features", category="managed-switches"),
    "l3_features": spec("Layer 3 / Routing Features", "Features", category="managed-switches"),
    "stacking": spec("Stacking Capability", "Features", category="managed-switches"),
    "acl_security": spec("ACL / Port Security", "Security", category="managed-switches"),
    "management_methods": spec("Management Methods", "Management", category="managed-switches"),
    "console_interfaces": spec("Console Ports", "Interfaces", category="managed-switches"),
    "management_interfaces": spec("Dedicated Management Ports", "Interfaces", category="managed-switches"),
    "switch_usb_interfaces": spec("USB Ports", "Interfaces", category="managed-switches"),
    "cpu": spec("CPU", "Hardware", category="managed-switches"),
    "flash_memory": spec("Flash Memory", "Hardware", category="managed-switches"),
    "dram_memory": spec("DRAM", "Hardware", category="managed-switches"),
    "power_supply": spec("Power Supply", "Power", category="managed-switches"),
    "fan_design": spec("Fan Design", "Physical", category="managed-switches"),
    "poe_configuration": spec("PoE Configuration", "PoE", category="managed-switches"),
    "stacking_bandwidth_gbps": spec("Stacking Bandwidth", "Stacking", "decimal", "Gbps", direction="higher", category="managed-switches"),
    "stacking_units": spec("Maximum Stacking Units", "Stacking", "integer", direction="higher", category="managed-switches"),
    "stacking_ports": spec("Stacking Ports", "Stacking", category="managed-switches"),
    "ip_interface_capacity": spec("IP Interface Capacity", "Capacity", category="managed-switches"),
    "arp_entry_capacity": spec("ARP Entry Capacity", "Capacity", category="managed-switches"),
    "routing_entry_capacity": spec("Routing Entry Capacity", "Capacity", category="managed-switches"),
    "igmp_group_capacity": spec("IGMP Group Capacity", "Capacity", category="managed-switches"),
    "lag_group_capacity": spec("LAG Group Capacity", "Capacity", category="managed-switches"),
    "sdn_support": spec("SDN Support", "Management", "boolean", category="managed-switches"),
    "dhcp_features": spec("DHCP Features", "Layer 3", category="managed-switches"),
    "stp_features": spec("STP / MSTP", "Layer 2", category="managed-switches"),
    "erps_support": spec("ERPS", "Layer 2", "boolean", category="managed-switches"),
    "mld_snooping": spec("MLD Snooping", "Multicast", "boolean", category="managed-switches"),
    "ospf_support": spec("OSPF", "Layer 3", "boolean", category="managed-switches"),
    "rip_support": spec("RIP", "Layer 3", "boolean", category="managed-switches"),
    "pbr_support": spec("Policy-Based Routing", "Layer 3", "boolean", category="managed-switches"),
    "vrrp_support": spec("VRRP", "Layer 3", "boolean", category="managed-switches"),
    "bfd_support": spec("BFD", "Layer 3", "boolean", category="managed-switches"),
    "macsec_support": spec("MACsec", "Security", "boolean", category="managed-switches"),
    "secure_boot": spec("Secure Boot", "Security", "boolean", category="managed-switches"),
    "vxlan_support": spec("VXLAN", "Data Center", "boolean", category="managed-switches"),
    "m_lag_support": spec("M-LAG", "Data Center", "boolean", category="managed-switches"),
    "ptp_support": spec("PTP", "Timing", "boolean", category="managed-switches"),
    "mpls_support": spec("MPLS", "Layer 3", "boolean", category="managed-switches"),
    "netconf_support": spec("NETCONF", "Management", "boolean", category="managed-switches"),
    "configuration_rollback": spec("Configuration Rollback", "Management", "boolean", category="managed-switches"),
    "hot_patching": spec("Hot Patching", "Reliability", "boolean", category="managed-switches"),
    "multicast_routing": spec("Multicast Routing", "Multicast", "boolean", category="managed-switches"),
    "segment_routing": spec("Segment Routing", "Layer 3", "boolean", category="managed-switches"),
    "dcb_support": spec("Data Center Bridging", "Data Center", "boolean", category="managed-switches"),
    "gre_tunnel": spec("GRE Tunnel", "Layer 3", "boolean", category="managed-switches"),
    "isp_features": spec("ISP Features", "Features", category="managed-switches"),
    "management_type": spec("Management Type", "Management", category="unmanaged-easy-smart-switches"),
    "vlan_support": spec("VLAN", "Features", category="unmanaged-easy-smart-switches"),
    "qos_support": spec("QoS", "Features", category="unmanaged-easy-smart-switches"),
    "link_aggregation": spec("Link Aggregation", "Features", category="unmanaged-easy-smart-switches"),
    "igmp_snooping": spec("IGMP Snooping", "Features", category="unmanaged-easy-smart-switches"),
    "port_mirroring": spec("Port Mirroring", "Diagnostics", category="unmanaged-easy-smart-switches"),
    "cable_test": spec("Cable Test", "Diagnostics", category="unmanaged-easy-smart-switches"),
    "extend_mode": spec("PoE Extend Mode", "PoE Features", "boolean", category="unmanaged-easy-smart-switches"),
    "poe_auto_recovery": spec("PoE Auto Recovery", "PoE Features", "boolean", category="unmanaged-easy-smart-switches"),
    "port_isolation": spec("Port Isolation", "Isolation", "boolean", category="unmanaged-easy-smart-switches"),
    "loop_prevention": spec("Loop Prevention", "Reliability", "boolean", category="unmanaged-easy-smart-switches"),
    "installation": spec("Desktop / Rack Installation", "Physical", category="unmanaged-easy-smart-switches"),
    "fanless": spec("Fanless Design", "Physical", "boolean"),
    # Accessories
    "accessory_connector_type": spec("Connector Type", "Interfaces", category="accessories"),
    "accessory_interface_type": spec("Interface Type", "Interfaces", category="accessories"),
    "accessory_data_rate_gbps": spec("Maximum Data Rate", "Performance", "decimal", "Gbps", direction="higher", category="accessories"),
    "accessory_input_power": spec("Input Power", "Power", category="accessories"),
    "accessory_output_power": spec("Output Power", "Power", category="accessories"),
    "accessory_poe_standard": spec("PoE Standard", "Power", category="accessories"),
    "accessory_power_w": spec("Maximum Output Power", "Power", "decimal", "W", direction="higher", category="accessories"),
    "accessory_wavelength_nm": spec("Wavelength", "Optical", "integer", "nm", category="accessories"),
    "accessory_fiber_mode": spec("Fiber Mode", "Optical", category="accessories"),
    "accessory_max_distance_km": spec("Maximum Transmission Distance", "Optical", "decimal", "km", direction="higher", category="accessories"),
    "accessory_cable_length_m": spec("Cable Length", "Physical", "decimal", "m", category="accessories"),
    "accessory_compatibility": spec("Compatible Products", "Compatibility", category="accessories"),
    "accessory_mounting_type": spec("Mounting Type", "Physical", category="accessories"),
    "accessory_rack_units": spec("Rack Units", "Physical", "decimal", "U", category="accessories"),
    "accessory_antenna_gain_dbi": spec("Antenna Gain", "Wireless", "decimal", "dBi", direction="higher", category="accessories"),
    "accessory_frequency_range": spec("Frequency Range", "Wireless", category="accessories"),
    # Environment and physical design
    "ip_rating": spec("IP / Weatherproof Rating", "Environment", filterable=True),
    "lightning_protection_kv": spec("Lightning / Surge Protection", "Environment", unit="kV", direction="higher"),
    "operating_temperature_c": spec("Operating Temperature", "Environment", unit="°C"),
    "dimensions_mm": spec("Dimensions", "Physical", unit="mm"),
}


def fields(*codes):
    return [(code, "p0") for code in codes]


COMMON_PHYSICAL = [
    ("max_power_consumption_w", "p2"),
    ("dimensions_mm", "p2"),
    ("operating_temperature_c", "p2"),
]


TEMPLATES = (
    {
        "name": "AP General",
        "category_slug": "access-point",
        "form_factor": "",
        "description": "Indoor ceiling, desktop and general-purpose access points.",
        "fields": fields(
            "supported_bands", "total_spatial_streams", "mimo_2g", "mimo_5g", "mimo_6g",
            "rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps", "max_channel_width_mhz",
            "ethernet_interfaces", "poe_input", "max_clients",
        ) + [
            ("antenna_type", "p1"), ("antenna_gain_dbi", "p1"), ("max_ssids", "p1"),
            ("centralized_management", "p1"), ("mesh_support", "p1"), ("fast_roaming", "p1"),
            ("wireless_security", "p1"),
        ] + COMMON_PHYSICAL,
    },
    {
        "name": "Outdoor AP",
        "category_slug": "access-point",
        "form_factor": "outdoor",
        "description": "Outdoor access points with weather, range and surge characteristics.",
        "fields": fields(
            "supported_bands", "total_spatial_streams", "rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps",
            "max_channel_width_mhz", "ethernet_interfaces", "poe_input", "max_clients", "ip_rating",
            "antenna_type", "antenna_gain_dbi", "wireless_range", "lightning_protection_kv",
        ) + [
            ("centralized_management", "p1"), ("mesh_support", "p1"),
            ("fast_roaming", "p1"), ("wireless_security", "p1"),
        ] + COMMON_PHYSICAL,
    },
    {
        "name": "Wall Plate AP",
        "category_slug": "access-point",
        "form_factor": "wall_plate",
        "description": "Wall-plate access points with downlink and PoE passthrough characteristics.",
        "fields": fields(
            "supported_bands", "total_spatial_streams", "rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps",
            "ethernet_interfaces", "poe_input", "poe_output", "max_clients",
        ) + [
            ("mimo_2g", "p1"), ("mimo_5g", "p1"), ("mimo_6g", "p1"),
            ("max_channel_width_mhz", "p1"), ("max_ssids", "p1"),
            ("centralized_management", "p1"), ("fast_roaming", "p1"),
            ("wireless_security", "p1"),
        ] + COMMON_PHYSICAL,
    },
    {
        "name": "Wireless Bridge General",
        "category_slug": "wireless-bridge",
        "form_factor": "",
        "description": "Point-to-point and point-to-multipoint wireless bridges.",
        "fields": fields(
            "supported_bands", "rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps", "wireless_range",
            "antenna_gain_dbi", "beamwidth", "ethernet_interfaces", "poe_input",
            "bridge_modes", "ip_rating", "lightning_protection_kv",
        ) + [("antenna_type", "p1"), ("max_bridge_pairs", "p1")] + COMMON_PHYSICAL,
    },
    {
        "name": "Gateway General",
        "category_slug": "gateway",
        "form_factor": "",
        "description": "Wired and security gateways with routing, VPN and session capacity.",
        "fields": fields(
            "wan_interfaces", "lan_interfaces", "ethernet_interfaces", "uplink_interfaces",
            "routing_throughput_mbps", "nat_throughput_mbps", "vpn_throughput_mbps",
            "concurrent_sessions", "vpn_tunnels", "wan_load_balancing", "sd_wan",
            "firewall_features", "vpn_protocols", "controller_management",
        ) + [("usb_interfaces", "p1"), ("lightning_protection_kv", "p1")] + COMMON_PHYSICAL,
    },
    {
        "name": "Managed General",
        "category_slug": "managed-switches",
        "form_factor": "",
        "description": "Managed switches with forwarding, PoE, L2/L3 and management capabilities.",
        "fields": fields(
            "ethernet_interfaces", "uplink_interfaces", "switching_capacity_gbps", "packet_forwarding_rate_mpps",
            "poe_configuration", "poe_standard", "poe_ports", "poe_budget_w",
            "max_poe_per_port_w",
        ) + [
            ("mac_address_table", "p1"), ("packet_buffer_mb", "p1"),
            ("console_interfaces", "p1"), ("management_interfaces", "p1"),
            ("switch_usb_interfaces", "p1"), ("cpu", "p1"), ("flash_memory", "p1"),
            ("dram_memory", "p1"), ("power_supply", "p1"), ("fan_design", "p1"),
            ("stacking_bandwidth_gbps", "p1"), ("stacking_units", "p1"),
            ("stacking_ports", "p1"), ("ip_interface_capacity", "p1"),
            ("arp_entry_capacity", "p1"), ("routing_entry_capacity", "p1"),
            ("igmp_group_capacity", "p1"), ("lag_group_capacity", "p1"),
            ("jumbo_frame_bytes", "p1"), ("vlan_count", "p1"),
            ("l2_features", "p1"), ("l3_features", "p1"), ("stacking", "p1"),
            ("acl_security", "p1"), ("management_methods", "p1"),
            ("redundant_power", "p1"), ("fanless", "p1"),
            ("sdn_support", "p2"), ("dhcp_features", "p2"), ("stp_features", "p2"),
            ("erps_support", "p2"), ("mld_snooping", "p2"), ("ospf_support", "p2"),
            ("rip_support", "p2"), ("pbr_support", "p2"), ("vrrp_support", "p2"),
            ("bfd_support", "p2"), ("macsec_support", "p2"), ("secure_boot", "p2"),
            ("vxlan_support", "p2"), ("m_lag_support", "p2"), ("ptp_support", "p2"),
            ("mpls_support", "p2"), ("netconf_support", "p2"),
            ("configuration_rollback", "p2"), ("hot_patching", "p2"),
            ("multicast_routing", "p2"), ("segment_routing", "p2"),
            ("dcb_support", "p2"), ("gre_tunnel", "p2"), ("isp_features", "p2"),
        ] + COMMON_PHYSICAL,
    },
    {
        "name": "Unmanaged / Easy Smart General",
        "category_slug": "unmanaged-easy-smart-switches",
        "form_factor": "",
        "description": "Unmanaged and Easy Smart switches focused on ports, PoE and basic controls.",
        "fields": fields(
            "ethernet_interfaces", "uplink_interfaces", "switching_capacity_gbps", "packet_forwarding_rate_mpps",
            "poe_standard", "poe_ports", "poe_budget_w", "max_poe_per_port_w", "management_type",
            "extend_mode", "poe_auto_recovery", "port_isolation", "loop_prevention",
        ) + [
            ("mac_address_table", "p1"), ("vlan_support", "p1"), ("qos_support", "p1"),
            ("link_aggregation", "p1"), ("igmp_snooping", "p1"),
            ("port_mirroring", "p1"), ("cable_test", "p1"),
            ("fanless", "p1"), ("installation", "p1"),
        ] + COMMON_PHYSICAL,
    },
)

AP_CORE_FIELDS = fields(
    "supported_bands",
    "total_spatial_streams",
    "rate_2g_mbps",
    "rate_5g_mbps",
    "rate_6g_mbps",
    "max_channel_width_mhz",
    "ethernet_interfaces",
    "poe_input",
    "max_clients",
)

MANAGED_SWITCH_CORE_FIELDS = fields(
    "ethernet_interfaces",
    "uplink_interfaces",
    "switching_capacity_gbps",
    "packet_forwarding_rate_mpps",
    "poe_standard",
    "poe_ports",
    "poe_budget_w",
)

ROUTER_CORE_FIELDS = fields(
    "wan_interfaces",
    "lan_interfaces",
    "routing_throughput_mbps",
    "nat_throughput_mbps",
    "vpn_throughput_mbps",
    "concurrent_sessions",
    "vpn_protocols",
)

ACCESSORY_COMMON_FIELDS = [
    ("accessory_compatibility", "p1"),
    ("dimensions_mm", "p2"),
    ("operating_temperature_c", "p2"),
]

TYPE_SPECIFIC_TEMPLATES = (
    {
        "name": "AP Ceiling Mount",
        "category_slug": "access-point",
        "form_factor": "ceiling",
        "description": "Ceiling-mounted indoor access points.",
        "fields": AP_CORE_FIELDS
        + [
            ("mimo_2g", "p1"),
            ("mimo_5g", "p1"),
            ("mimo_6g", "p1"),
            ("antenna_type", "p1"),
            ("antenna_gain_dbi", "p1"),
            ("centralized_management", "p1"),
            ("mesh_support", "p1"),
            ("fast_roaming", "p1"),
        ]
        + COMMON_PHYSICAL,
    },
    {
        "name": "AP Wall Mount",
        "category_slug": "access-point",
        "form_factor": "wall",
        "description": "Wall-mounted access points.",
        "fields": AP_CORE_FIELDS
        + [
            ("antenna_type", "p1"),
            ("antenna_gain_dbi", "p1"),
            ("centralized_management", "p1"),
        ]
        + COMMON_PHYSICAL,
    },
    {
        "name": "AP Desktop",
        "category_slug": "access-point",
        "form_factor": "desktop",
        "description": "Desktop access points.",
        "fields": AP_CORE_FIELDS
        + [
            ("poe_output", "p1"),
            ("antenna_type", "p1"),
            ("centralized_management", "p1"),
        ]
        + COMMON_PHYSICAL,
    },
    {
        "name": "AP Extender",
        "category_slug": "access-point",
        "form_factor": "extender",
        "description": "Wireless range extenders.",
        "fields": fields(
            "supported_bands",
            "rate_2g_mbps",
            "rate_5g_mbps",
            "rate_6g_mbps",
            "max_channel_width_mhz",
        )
        + [
            ("antenna_type", "p1"),
            ("mesh_support", "p1"),
            ("wireless_security", "p1"),
        ]
        + COMMON_PHYSICAL,
    },
    {
        "name": "Managed L2",
        "category_slug": "managed-switches",
        "form_factor": "l2",
        "description": "Layer 2 managed switches.",
        "fields": MANAGED_SWITCH_CORE_FIELDS
        + [
            ("mac_address_table", "p1"),
            ("vlan_count", "p1"),
            ("l2_features", "p1"),
            ("stp_features", "p1"),
            ("acl_security", "p1"),
            ("management_methods", "p1"),
            ("fanless", "p1"),
        ]
        + COMMON_PHYSICAL,
    },
    {
        "name": "Managed L2 Plus",
        "category_slug": "managed-switches",
        "form_factor": "l2_plus",
        "description": "Layer 2+ switches with static routing and enhanced management.",
        "fields": MANAGED_SWITCH_CORE_FIELDS
        + [
            ("mac_address_table", "p1"),
            ("vlan_count", "p1"),
            ("l2_features", "p1"),
            ("l3_features", "p1"),
            ("ip_interface_capacity", "p1"),
            ("routing_entry_capacity", "p1"),
            ("stp_features", "p1"),
            ("dhcp_features", "p1"),
            ("acl_security", "p1"),
            ("management_methods", "p1"),
        ]
        + COMMON_PHYSICAL,
    },
    {
        "name": "Managed L3",
        "category_slug": "managed-switches",
        "form_factor": "l3",
        "description": "Layer 3 managed switches with dynamic routing.",
        "fields": MANAGED_SWITCH_CORE_FIELDS
        + [
            ("l2_features", "p1"),
            ("l3_features", "p1"),
            ("ip_interface_capacity", "p1"),
            ("routing_entry_capacity", "p1"),
            ("ospf_support", "p1"),
            ("rip_support", "p1"),
            ("pbr_support", "p1"),
            ("vrrp_support", "p1"),
            ("multicast_routing", "p1"),
            ("stacking", "p1"),
            ("stacking_bandwidth_gbps", "p1"),
            ("management_methods", "p1"),
        ]
        + COMMON_PHYSICAL,
    },
    {
        "name": "Unmanaged Switch",
        "category_slug": "unmanaged-easy-smart-switches",
        "form_factor": "unmanaged",
        "description": "Plug-and-play unmanaged switches.",
        "fields": fields(
            "ethernet_interfaces",
            "uplink_interfaces",
            "switching_capacity_gbps",
            "packet_forwarding_rate_mpps",
            "poe_standard",
            "poe_ports",
            "poe_budget_w",
            "extend_mode",
            "poe_auto_recovery",
            "port_isolation",
            "loop_prevention",
        )
        + [
            ("fanless", "p1"),
            ("installation", "p1"),
        ]
        + COMMON_PHYSICAL,
    },
    {
        "name": "Easy Smart Switch",
        "category_slug": "unmanaged-easy-smart-switches",
        "form_factor": "easy_smart",
        "description": "Easy Smart switches with VLAN, QoS, and diagnostics.",
        "fields": fields(
            "ethernet_interfaces",
            "uplink_interfaces",
            "switching_capacity_gbps",
            "packet_forwarding_rate_mpps",
            "management_type",
            "vlan_support",
            "qos_support",
            "igmp_snooping",
            "port_mirroring",
            "cable_test",
            "poe_standard",
            "poe_ports",
            "poe_budget_w",
        )
        + [
            ("link_aggregation", "p1"),
            ("fanless", "p1"),
            ("installation", "p1"),
        ]
        + COMMON_PHYSICAL,
    },
    {
        "name": "Wired Router",
        "category_slug": "gateway",
        "form_factor": "wired_router",
        "description": "Wired VPN and security routers.",
        "fields": ROUTER_CORE_FIELDS
        + [
            ("vpn_tunnels", "p1"),
            ("wan_load_balancing", "p1"),
            ("sd_wan", "p1"),
            ("firewall_features", "p1"),
            ("controller_management", "p1"),
        ]
        + COMMON_PHYSICAL,
    },
    {
        "name": "Wireless Router",
        "category_slug": "gateway",
        "form_factor": "wireless_router",
        "description": "Routers with integrated Wi-Fi.",
        "fields": ROUTER_CORE_FIELDS
        + fields(
            "router_wifi_standard",
            "router_supported_bands",
            "router_wireless_rate_mbps",
        )
        + [("controller_management", "p1")]
        + COMMON_PHYSICAL,
    },
    {
        "name": "Cellular Router",
        "category_slug": "gateway",
        "form_factor": "cellular_router",
        "description": "Indoor 4G and 5G routers.",
        "fields": ROUTER_CORE_FIELDS
        + fields(
            "cellular_standard",
            "sim_interfaces",
            "cellular_downlink_mbps",
        )
        + [("router_wifi_standard", "p1"), ("router_supported_bands", "p1")]
        + COMMON_PHYSICAL,
    },
    {
        "name": "Outdoor Cellular Router",
        "category_slug": "gateway",
        "form_factor": "outdoor_cellular_router",
        "description": "Outdoor cellular routers with environmental protection.",
        "fields": ROUTER_CORE_FIELDS
        + fields(
            "cellular_standard",
            "sim_interfaces",
            "cellular_downlink_mbps",
            "ip_rating",
            "lightning_protection_kv",
        )
        + COMMON_PHYSICAL,
    },
    {
        "name": "Integrated Gateway",
        "category_slug": "gateway",
        "form_factor": "integrated_gateway",
        "description": "Controller, switch, and PoE integrated gateways.",
        "fields": ROUTER_CORE_FIELDS
        + fields(
            "controller_management",
            "router_poe_ports",
            "router_poe_budget_w",
        )
        + [("ethernet_interfaces", "p1"), ("usb_interfaces", "p1")]
        + COMMON_PHYSICAL,
    },
    {
        "name": "PoE Injector",
        "category_slug": "accessories",
        "form_factor": "poe_injector",
        "description": "PoE injectors and adapters.",
        "fields": fields(
            "accessory_interface_type",
            "accessory_input_power",
            "accessory_output_power",
            "accessory_poe_standard",
            "accessory_power_w",
            "accessory_data_rate_gbps",
        )
        + ACCESSORY_COMMON_FIELDS,
    },
    {
        "name": "Power Supply",
        "category_slug": "accessories",
        "form_factor": "power_supply",
        "description": "Power supply and replaceable power modules.",
        "fields": fields(
            "accessory_input_power",
            "accessory_output_power",
            "accessory_power_w",
            "accessory_compatibility",
        )
        + COMMON_PHYSICAL,
    },
    {
        "name": "Media Converter",
        "category_slug": "accessories",
        "form_factor": "media_converter",
        "description": "Copper and fiber media converters.",
        "fields": fields(
            "accessory_interface_type",
            "accessory_connector_type",
            "accessory_data_rate_gbps",
            "accessory_fiber_mode",
            "accessory_max_distance_km",
            "accessory_input_power",
        )
        + ACCESSORY_COMMON_FIELDS,
    },
    {
        "name": "Optical Module",
        "category_slug": "accessories",
        "form_factor": "optical_module",
        "description": "Pluggable optical transceiver modules.",
        "fields": fields(
            "accessory_interface_type",
            "accessory_connector_type",
            "accessory_data_rate_gbps",
            "accessory_wavelength_nm",
            "accessory_fiber_mode",
            "accessory_max_distance_km",
        )
        + ACCESSORY_COMMON_FIELDS,
    },
    {
        "name": "DAC Cable",
        "category_slug": "accessories",
        "form_factor": "dac_cable",
        "description": "Direct-attach copper cables.",
        "fields": fields(
            "accessory_interface_type",
            "accessory_data_rate_gbps",
            "accessory_cable_length_m",
        )
        + ACCESSORY_COMMON_FIELDS,
    },
    {
        "name": "Mounting Accessory",
        "category_slug": "accessories",
        "form_factor": "mounting",
        "description": "Rack, wall, and magnetic mounting accessories.",
        "fields": fields(
            "accessory_mounting_type",
            "accessory_compatibility",
        )
        + [("accessory_rack_units", "p1"), ("dimensions_mm", "p1")],
    },
    {
        "name": "Accessory Chassis",
        "category_slug": "accessories",
        "form_factor": "chassis",
        "description": "Accessory and media-converter chassis.",
        "fields": fields(
            "accessory_rack_units",
            "accessory_compatibility",
            "accessory_input_power",
        )
        + [("dimensions_mm", "p1"), ("operating_temperature_c", "p2")],
    },
    {
        "name": "Antenna",
        "category_slug": "accessories",
        "form_factor": "antenna",
        "description": "External antennas and antenna accessories.",
        "fields": fields(
            "accessory_connector_type",
            "accessory_frequency_range",
            "accessory_antenna_gain_dbi",
            "accessory_compatibility",
        )
        + COMMON_PHYSICAL,
    },
    {
        "name": "Junction Box",
        "category_slug": "accessories",
        "form_factor": "junction_box",
        "description": "Outdoor junction and cable-management boxes.",
        "fields": fields(
            "accessory_compatibility",
            "ip_rating",
            "accessory_mounting_type",
        )
        + COMMON_PHYSICAL,
    },
    {
        "name": "Accessories General",
        "category_slug": "accessories",
        "form_factor": "",
        "description": "Fallback structure for other accessories.",
        "fields": fields(
            "accessory_interface_type",
            "accessory_connector_type",
            "accessory_compatibility",
        )
        + COMMON_PHYSICAL,
    },
)

TEMPLATES = TEMPLATES + TYPE_SPECIFIC_TEMPLATES


LIST_FIELDS_BY_CATEGORY = {
    "access-point": ("supported_bands", "total_spatial_streams", "ethernet_interfaces"),
    "wireless-bridge": ("wireless_range", "antenna_gain_dbi", "ethernet_interfaces"),
    "gateway": ("ethernet_interfaces", "vpn_throughput_mbps", "concurrent_sessions"),
    "managed-switches": ("ethernet_interfaces", "switching_capacity_gbps", "poe_budget_w"),
    "unmanaged-easy-smart-switches": ("ethernet_interfaces", "poe_budget_w", "fanless"),
    "accessories": ("accessory_interface_type", "accessory_compatibility", "dimensions_mm"),
}
