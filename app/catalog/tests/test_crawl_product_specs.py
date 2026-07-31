from django.test import SimpleTestCase

from catalog.management.commands.crawl_product_specs import extract_specs, model_token_present


class ExtractSpecsTests(SimpleTestCase):
    def test_access_point_extracts_band_specific_rates_without_cross_matching(self):
        text = """
        AX1800 4-Stream Ceiling Mount Access Point
        Frequency: 2.4 GHz and 5 GHz
        Signal Rate
        5 GHz: Up to 1201 Mbps
        2.4 GHz: Up to 574 Mbps
        Concurrent Clients: 250+
        Dimensions: 160 × 160 × 33.6 mm
        Operating Temperature: 0–40 °C • Storage Temperature: -40–70 °C
        """

        specs = extract_specs(text, "access-point")

        self.assertEqual(specs["rate_2g_mbps"][1], 574)
        self.assertEqual(specs["rate_5g_mbps"][1], 1201)
        self.assertEqual(specs["dimensions_mm"][1], "160 × 160 × 33.6 mm")
        self.assertEqual(specs["operating_temperature_c"][1], "0–40 °C")

    def test_switch_extracts_comparison_specs(self):
        text = """
        Interface
        8× 100Mbps/1Gbps/2.5Gbps/5Gbps/10Gbps RJ45 Ports
        Switching Capacity: 160 Gbps
        Packet Forwarding Rate: 119.0 Mpps
        MAC Address Table: 16 K
        Total PoE Budget: 500 W
        Fanless
        """

        specs = extract_specs(text, "managed-switches")

        self.assertIn("8×", specs["ethernet_interfaces"][1])
        self.assertEqual(specs["switching_capacity_gbps"][1], 160.0)
        self.assertEqual(specs["poe_budget_w"][1], 500.0)

    def test_gateway_rejects_unrelated_interface_label_value(self):
        text = "Ports\nCentralized Cloud\nVPN Throughput: 1006 Mbps"

        specs = extract_specs(text, "gateway")

        self.assertNotIn("ethernet_interfaces", specs)
        self.assertEqual(specs["vpn_throughput_mbps"][1], 1006)

    def test_access_point_extracts_template_features(self):
        text = """
        2.4 GHz: Up to 574 Mbps, 2x2 MIMO
        5 GHz: Up to 2402 Mbps, 4x4 MU-MIMO
        Ethernet Ports: 1x 2.5G RJ45
        Antenna Type: Internal Omni
        Maximum SSIDs: 16
        Omada SDN centralized management
        Wireless Mesh, 802.11k/802.11v/802.11r
        Wireless Security: WPA3-Enterprise
        """

        specs = extract_specs(text, "access-point")

        self.assertEqual(specs["ethernet_interfaces"][1], "1x 2.5G RJ45")
        self.assertEqual(specs["mimo_2g"][1], "2x2 MIMO")
        self.assertEqual(specs["mimo_5g"][1], "4x4 MU-MIMO")
        self.assertEqual(specs["max_ssids"][1], 16)
        self.assertTrue(specs["mesh_support"][1])
        self.assertIn("802.11r", specs["fast_roaming"][1])

    def test_switch_extracts_extended_template_fields(self):
        text = """
        24 PoE+ ports
        802.3af/at
        Uplink Ports: 4x 10G SFP+
        Maximum PoE per Port: 30 W
        Packet Buffer Memory: 1.5 MB
        Jumbo Frame: 9 KB
        Maximum VLANs: 4094
        Layer 2 Features: STP, RSTP, MSTP
        Management Methods: Web, CLI, SNMP
        Redundant Power Supply
        """

        specs = extract_specs(text, "managed-switches")

        self.assertEqual(specs["poe_ports"][1], 24)
        self.assertEqual(specs["poe_standard"][1], "802.3af / 802.3at")
        self.assertEqual(specs["max_poe_per_port_w"][1], 30.0)
        self.assertEqual(specs["packet_buffer_mb"][1], 1.5)
        self.assertEqual(specs["jumbo_frame_bytes"][1], 9216)
        self.assertEqual(specs["vlan_count"][1], 4094)
        self.assertTrue(specs["redundant_power"][1])

    def test_gateway_extracts_interfaces_and_throughput(self):
        text = """
        WAN Ports: 2x 2.5G RJ45
        LAN Ports: 8x Gigabit RJ45
        NAT Throughput: 2.5 Gbps
        Routing Throughput: 1800 Mbps
        VPN Tunnels: 100
        Multi-WAN Load Balancing
        """

        specs = extract_specs(text, "gateway")

        self.assertEqual(specs["wan_interfaces"][1], "2x 2.5G RJ45")
        self.assertEqual(specs["lan_interfaces"][1], "8x Gigabit RJ45")
        self.assertEqual(specs["nat_throughput_mbps"][1], 2500)
        self.assertEqual(specs["routing_throughput_mbps"][1], 1800)
        self.assertEqual(specs["vpn_tunnels"][1], 100)
        self.assertTrue(specs["wan_load_balancing"][1])

    def test_switch_does_not_treat_per_port_watts_as_port_count(self):
        specs = extract_specs(
            "Maximum PoE power: 30W for each PoE port\nPacket Buffer Memory: 4 Mb",
            "managed-switches",
        )

        self.assertNotIn("poe_ports", specs)
        self.assertEqual(specs["packet_buffer_mb"][1], 0.5)

    def test_supported_bands_follow_product_rates_not_unrelated_page_text(self):
        specs = extract_specs(
            "2.4 GHz: Up to 300 Mbps\nRelated products support 5 GHz",
            "access-point",
        )

        self.assertEqual(specs["supported_bands"][1], "2.4 GHz")

    def test_model_token_does_not_accept_longer_sibling_model(self):
        self.assertTrue(model_token_present("ER605", "TP-Link ER605 | Omada Gateway"))
        self.assertFalse(model_token_present("ER605", "TP-Link ER605W | Omada Gateway"))
