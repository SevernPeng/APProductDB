import io

from django.test import SimpleTestCase
from PIL import Image
from unittest.mock import patch

from catalog.management.commands.crawl_product_specs import (
    aruba_switch_sku_matches,
    crawl_product,
    encode_http_url,
    extract_product_image_url,
    extract_specs,
    linked_official_documents,
    lookup_model_name,
    model_token_present,
    official_image_redirect_allowed,
    parse_reyee_challenge_cookie,
    trendnet_support_image_url,
    verified_image_suffix,
)


class ExtractSpecsTests(SimpleTestCase):
    def test_allows_only_meraki_document_image_cdn_redirect(self):
        original = "https://documentation.meraki.com/@api/deki/files/25987/MR28_front.png"
        self.assertTrue(official_image_redirect_allowed(
            "Meraki", original, "https://files.mtstatic.com/site_13505/25987/0/webview",
        ))
        self.assertFalse(official_image_redirect_allowed(
            "Meraki", original, "https://files.mtstatic.com/site_99999/25987/0/webview",
        ))

    @patch("catalog.management.commands.crawl_product_specs.fetch_url")
    def test_finds_trendnet_version_page_image_for_model(self, fetch):
        fetch.return_value = (
            "https://www.trendnet.com/support/versions.asp?pID=TPE-P521ES",
            "text/html",
            b'''<title>TPE-P521ES Product Versions</title>
                <img src="https://www.trendnet.com/images/products/photos/TPE-P521ES_v2/front.webp"
                     alt="TPE-P521ES product">''',
        )
        self.assertEqual(
            trendnet_support_image_url("TPE-P521ES"),
            "https://www.trendnet.com/images/products/photos/TPE-P521ES_v2/front.webp",
        )

    def test_validates_png_bytes_despite_wrong_server_content_type(self):
        data = io.BytesIO()
        Image.new("RGB", (2, 2)).save(data, format="PNG")
        self.assertEqual(verified_image_suffix(data.getvalue()), ".png")
        with self.assertRaises(ValueError):
            verified_image_suffix(b"not an image")

    def test_does_not_assign_combined_band_mimo_to_each_radio(self):
        specs = extract_specs(
            "Tri-radio or dual-radio, 6ss (2.4 GHz, 5 GHz, 6 GHz or 2.4 GHz + 5 GHz (4x4:4))",
            "access-point",
        )
        self.assertNotIn("mimo_2g", specs)
        self.assertNotIn("mimo_5g", specs)
        self.assertNotIn("mimo_6g", specs)
        self.assertNotIn("total_spatial_streams", specs)

    def test_accepts_aruba_switch_sku_only_with_matching_family_and_title(self):
        self.assertTrue(aruba_switch_sku_matches(
            "6200F (JL725A)",
            "https://buy.hpe.com/us/en/networking/switches/p/jl725a",
            "HPE Aruba Networking CX 6200F 24G Class4 PoE Switch | HPE Store",
        ))
        self.assertFalse(aruba_switch_sku_matches(
            "1960 (JL807A)",
            "https://buy.hpe.com/us/en/p/jl807a",
            "Search | HPE Store",
        ))
        self.assertFalse(aruba_switch_sku_matches(
            "6200F (JL725A)",
            "https://buy.hpe.com/us/en/networking/switches/p/jl726a",
            "HPE Aruba Networking CX 6200F 24G Switch",
        ))

    def test_encodes_spaces_and_unicode_in_official_image_url(self):
        self.assertEqual(
            encode_http_url("https://eo-sgp-cos.ruijie.com/products/Frame 1-正面.png"),
            "https://eo-sgp-cos.ruijie.com/products/Frame%201-%E6%AD%A3%E9%9D%A2.png",
        )

    def test_parses_reyee_javascript_challenge_cookie(self):
        challenge = b'''<script>
          var e={WTKkN:1020901534,bOYDu:124729792,
                 dtzqS:function(a,n){return a+n},wyeCN:26531117,
                 pCQRM:function(a){return a()}},t=0;
          document.cookie="__tst_status="+a(0)+"#;";
          t=a.x(t,1252655104); t+="EO_Bot_Ssid=";
        </script>'''

        self.assertEqual(
            parse_reyee_challenge_cookie(challenge),
            "__tst_status=1172162443#; EO_Bot_Ssid=1252655104",
        )

    def test_extracts_first_model_specific_official_product_image(self):
        page = b'''
          <img src="https://eo-sgp-cos.ruijie.com/site/logo.svg" alt="logo">
          <img data-index="0"
               src="https://eo-sgp-cos.ruijie.com/products/rap72pro-front.png"
               alt="RG-RAP72Pro - 1">
          <img data-index="1"
               src="https://eo-sgp-cos.ruijie.com/products/rap72pro-back.png"
               alt="RG-RAP72Pro - 2">
        '''

        self.assertEqual(
            extract_product_image_url(
                "https://reyee.ruijie.com/en-global/products/rg-rap72pro/",
                page,
                ("reyee.ruijie.com", "ruijie.com"),
                "RG-RAP72Pro",
            ),
            "https://eo-sgp-cos.ruijie.com/products/rap72pro-front.png",
        )

    def test_extracts_ruijie_primary_upload_without_alt_text(self):
        page = b'''
          <img src="https://eo-sgp-cos.ruijie.com/site/logo.svg" alt="">
          <img src="https://eo-sgp-cos.ruijie.com/FU/Upload/Product/2020/main.jpg">
          <img src="https://eo-sgp-cos.ruijie.com/FU/UIA/Product/feature.jpg">
        '''

        self.assertEqual(
            extract_product_image_url(
                "https://www.ruijie.com/en-global/products/wireless/ap110-l",
                page,
                ("ruijie.com",),
                "RG-AP110-L",
            ),
            "https://eo-sgp-cos.ruijie.com/FU/Upload/Product/2020/main.jpg",
        )

    def test_extracts_extensionless_netgear_cdn_image(self):
        page = b'''
          <meta property="og:image"
                content="https://assets.netgear.com/transform/uuid/agm732f_productcarousel_1">
        '''

        self.assertEqual(
            extract_product_image_url(
                "https://www.netgear.com/business/accessories/agm732f/",
                page,
                ("netgear.com",),
                "AGM732F",
            ),
            "https://assets.netgear.com/transform/uuid/agm732f_productcarousel_1",
        )

    def test_extracts_hpe_product_image_without_model_in_filename(self):
        page = b'''<meta property="og:image"
            content="https://assets.ext.hpe.com/is/image/hpedam/s00013162?$product$#.png">'''
        self.assertEqual(
            extract_product_image_url(
                "https://buy.hpe.com/us/en/networking/wireless-devices/wlan-access-points/ap-735/p/s1g43a",
                page,
                ("arubanetworks.com", "hpe.com"),
                "AP-735",
            ),
            "https://assets.ext.hpe.com/is/image/hpedam/s00013162?$product$#.png",
        )

    def test_rejects_generic_social_logo_on_download_listing(self):
        page = b'''<meta property="og:image"
            content="https://www.zyxel.com/library/assets/homepage/Zyxel_Networks_logo_color.png">'''
        self.assertEqual(
            extract_product_image_url(
                "https://www.zyxel.com/global/en/support/download?model=xmg1930-30",
                page,
                ("zyxel.com",),
                "XMG1930-30",
            ),
            "",
        )

    def test_extracts_huawei_ekit_primary_image_from_nuxt_data(self):
        page = b'''<script id="__NUXT_DATA__" type="application/json">
            ["AP361","https://ekit.huawei.com/epartner/s3/product.png",{"name":0,"pictureUrl":1}]
            </script>'''
        self.assertEqual(
            extract_product_image_url(
                "https://ekit.huawei.com/brand/en/product/sme-network/wlan/123",
                page,
                ("huawei.com",),
                "eKit AP361",
            ),
            "https://ekit.huawei.com/epartner/s3/product.png",
        )

    def test_prefers_grandstream_gallery_front_over_social_image(self):
        page = b'''<meta property="og:image" content="https://www.grandstream.com/hubfs/social-image-GWN7670E-no-text.png">
            <img class="zoom-img" src="https://www.grandstream.com/hubfs/GWN7670E_2.png">
            <img class="zoom-img" src="https://www.grandstream.com/hubfs/GWN7670E_1.png">'''
        self.assertEqual(
            extract_product_image_url(
                "https://www.grandstream.com/products/networking-solutions/indoor-wifi-access-points/product/gwn7670e",
                page,
                ("grandstream.com",),
                "GWN7670E",
            ),
            "https://www.grandstream.com/hubfs/GWN7670E_1.png",
        )

    def test_dlink_prefers_exact_model_gallery_over_feature_and_sibling_images(self):
        page = b'''<meta property="og:image" content="https://www.dlink.com/en/-/media/product-pages/dis/210g-series/210g-06p/assets/dis210g06p-uninterrupted-power.png">
            <img src="https://www.dlink.com/en/-/media/product-pages/dis/210g-series/210g-06p/product-images/dis210g06pa1image-hfront.png">
            <img src="https://www.dlink.com/en/-/media/product-pages/dis/210g-series/210g-06/product-images/dis210g06a1image-hfront.png">'''

        self.assertEqual(
            extract_product_image_url(
                "https://www.dlink.com/en/products/dis-210g-06p", page, ("dlink.com",), "DIS-210G-06P"
            ),
            "https://www.dlink.com/en/-/media/product-pages/dis/210g-series/210g-06p/product-images/dis210g06pa1image-hfront.png",
        )

    def test_extracts_ruckus_official_image_server_url(self):
        image_url = (
            "https://productresources.vistancenetworks.com/admin/ImageServer.php?"
            "ID=abc&downloadname=RUCKUS%2BR575%2Bright.png&preset=7"
        )
        page = f'<meta property="og:image" content="{image_url}">'.encode()

        self.assertEqual(
            extract_product_image_url(
                "https://www.ruckusnetworks.com/products/wireless-access-points/r575/",
                page,
                ("ruckusnetworks.com", "vistancenetworks.com"),
                "R575",
            ),
            image_url.replace("%2B", "+"),
        )

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

    def test_access_point_merges_uplink_into_ethernet_and_extracts_power_method(self):
        specs = extract_specs(
            "Uplink: GbE\nPower Method: PoE\n2.4 GHz: Up to 574 Mbps",
            "access-point",
        )

        self.assertEqual(specs["ethernet_interfaces"][1], "Uplink: GbE")
        self.assertEqual(specs["power_method"][1], "PoE")
        self.assertNotIn("uplink_interface", specs)

    def test_access_point_combines_poe_and_dc_power(self):
        specs = extract_specs(
            "IEEE 802.3at PoE. Power Supply: 12 V DC / 1.5 A",
            "access-point",
        )

        self.assertIn("PoE (802.3at)", specs["power_method"][1])
        self.assertIn("12 V DC", specs["power_method"][1])

    def test_wifi_standard_alone_does_not_infer_supported_bands(self):
        specs = extract_specs("Tri-Band Wi-Fi 7 access point", "access-point")

        self.assertNotIn("supported_bands", specs)

    def test_reyee_key_specifications_extract_exact_radio_values(self):
        specs = extract_specs(
            """
            Radio design
            Dual-radio
            4 spatial streams
            2.4 GHz: 2 x 2, MU-MIMO
            5 GHz: 2 x 2, MU-MIMO
            Maximum wireless data rate
            2974 Mbps
            6 GHz wireless data rate
            No
            5 GHz wireless data rate
            2401 Mbps
            2.4 GHz wireless data rate
            573 Mbps
            Antenna
            Antenna
            2.4 GHz: 2 built-in omnidirectional antennas
            5 GHz: 3 built-in omnidirectional antennas
            Dimensions and Weight
            Maximum number of associated wireless clients
            64 (2.4 GHz)
            512 (5 GHz)
            512 (2.4 GHz and 5 GHz enabled)
            Maximum number of devices that can be managed
            300
            Smart K/V Roaming
            """,
            "access-point",
        )

        self.assertEqual(specs["rate_2g_mbps"][1], 573)
        self.assertEqual(specs["rate_5g_mbps"][1], 2401)
        self.assertNotIn("rate_6g_mbps", specs)
        self.assertEqual(specs["supported_bands"][1], "2.4 GHz / 5 GHz")
        self.assertEqual(specs["max_clients"][1], 512)
        self.assertIn("2.4 GHz: 2 built-in", specs["antenna_type"][1])
        self.assertIn("802.11v", specs["fast_roaming"][1])

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

    def test_gateway_extracts_common_tp_link_datasheet_fields(self):
        text = """
        2× 2.5G RJ45 WAN/LAN Ports
        8× Gigabit RJ45 LAN Ports
        Centralized cloud management with Omada SDN
        VPN: IPsec / SSL / OpenVPN / WireGuard / L2TP / PPTP / GRE
        PoE Ports: 8
        PoE Power Budget: 110 W
        802.3af/at
        """

        specs = extract_specs(text, "gateway")

        self.assertIn("WAN/LAN", specs["wan_interfaces"][1])
        self.assertEqual(specs["controller_management"][1], "Omada SDN")
        self.assertIn("WireGuard", specs["vpn_protocols"][1])
        self.assertEqual(specs["router_poe_ports"][1], 8)
        self.assertEqual(specs["router_poe_budget_w"][1], 110)

    def test_accessory_extracts_optical_and_cable_specs(self):
        text = """
        Form Factor: SFP+
        Connector Type: LC duplex
        Maximum Data Rate: 10 Gbps
        Wavelength: 1310 nm
        Fiber Mode: Single-mode fiber (SMF)
        Maximum Transmission Distance: 10 km
        """

        specs = extract_specs(text, "accessories")

        self.assertEqual(specs["accessory_interface_type"][1], "SFP+")
        self.assertEqual(specs["accessory_connector_type"][1], "LC duplex")
        self.assertEqual(specs["accessory_data_rate_gbps"][1], 10)
        self.assertEqual(specs["accessory_wavelength_nm"][1], 1310)
        self.assertEqual(specs["accessory_fiber_mode"][1], "Single-mode")
        self.assertEqual(specs["accessory_max_distance_km"][1], 10)

    def test_accessory_extracts_poe_power_specs(self):
        text = """
        Input Power: 100-240 V AC, 50/60 Hz
        Output Power: 54 V DC, maximum 60 W
        IEEE 802.3af/at/bt
        """

        specs = extract_specs(text, "accessories")

        self.assertIn("802.3af", specs["accessory_poe_standard"][1])
        self.assertIn("100-240 V AC", specs["accessory_input_power"][1])
        self.assertIn("54 V DC", specs["accessory_output_power"][1])

    def test_switch_does_not_treat_per_port_watts_as_port_count(self):
        specs = extract_specs(
            "Maximum PoE power: 30W for each PoE port\nPacket Buffer Memory: 4 Mb",
            "managed-switches",
        )

        self.assertNotIn("poe_ports", specs)
        self.assertEqual(specs["packet_buffer_mb"][1], 0.5)

    def test_switch_extracts_poe_power_budget_wording(self):
        specs = extract_specs(
            "PoE Power Budget: 65 W; supports up to 30 W PoE output per port",
            "unmanaged-easy-smart-switches",
        )

        self.assertEqual(specs["poe_budget_w"][1], 65)
        self.assertEqual(specs["max_poe_per_port_w"][1], 30)

    def test_unmanaged_switch_extracts_advanced_features_and_forwarding_method(self):
        specs = extract_specs(
            """
            Advanced Features
            802.3X Flow Control
            802.1p/DSCP QoS
            IGMP Snooping V1/V2/V3
            Transmission Method: Store-And-Forward
            """,
            "unmanaged-easy-smart-switches",
        )

        self.assertEqual(specs["flow_control"][1], "802.3X Flow Control")
        self.assertEqual(specs["qos_support"][1], "802.1p/DSCP QoS")
        self.assertIn("IGMP Snooping", specs["igmp_snooping"][1])
        self.assertEqual(specs["transmission_method"][1], "Store and Forward")

    def test_datasheet_discovery_unwraps_tp_link_pdf_viewer(self):
        direct = "https://static.tp-link.com/upload/product-overview/Datasheet_EAP773.pdf"
        viewer = (
            "https://static.tp-link.com/pdf-viewer/web/viewer.html?file="
            "https%3A%2F%2Fstatic.tp-link.com%2Fupload%2Fproduct-overview%2FDatasheet_EAP773.pdf"
        )
        html = f'<iframe src="{viewer}"></iframe>'.encode()

        urls = linked_official_documents(
            "https://www.tp-link.com/en/business-networking/omada-wifi-ceiling-mount/eap773/",
            html,
            ("tp-link.com",),
            "EAP773",
        )

        self.assertEqual(urls, [direct])

    def test_supported_bands_follow_product_rates_not_unrelated_page_text(self):
        specs = extract_specs(
            "2.4 GHz: Up to 300 Mbps\nRelated products support 5 GHz",
            "access-point",
        )

        self.assertEqual(specs["supported_bands"][1], "2.4 GHz")

    def test_model_token_does_not_accept_longer_sibling_model(self):
        self.assertTrue(model_token_present("ER605", "TP-Link ER605 | Omada Gateway"))
        self.assertFalse(model_token_present("ER605", "TP-Link ER605W | Omada Gateway"))

    def test_lookup_model_removes_embedded_hardware_version_suffix(self):
        self.assertEqual(lookup_model_name("EAP211-Bridge KIT 3.0"), "EAP211-Bridge KIT")

    @patch("catalog.management.commands.crawl_product_specs.pdf_to_text")
    @patch("catalog.management.commands.crawl_product_specs.linked_official_documents")
    @patch("catalog.management.commands.crawl_product_specs.fetch_url")
    def test_official_datasheet_values_take_priority_per_field(self, fetch_url, linked_documents, pdf_to_text):
        page_url = "https://techspecs.ui.com/unifi/wifi/u6-plus"
        pdf_url = "https://dl.ui.com/ds/u6%2B_ds.pdf"
        fetch_url.side_effect = [
            (page_url, "text/html", b"<title>Ubiquiti U6+</title>2.4 GHz: Up to 300 Mbps"),
            (pdf_url, "application/pdf", b"%PDF-fake"),
        ]
        linked_documents.return_value = [pdf_url]
        pdf_to_text.return_value = "U6+ 2.4 GHz: Up to 573.5 Mbps"

        result = crawl_product((1, "Ubiquiti", "U6+", "access-point", page_url))

        self.assertEqual(result["specs"]["rate_2g_mbps"][1], 573.5)
        self.assertEqual(result["spec_sources"]["rate_2g_mbps"], pdf_url)

    @patch("catalog.management.commands.crawl_product_specs.fetch_url")
    def test_pdf_url_returning_html_is_rejected(self, fetch_url):
        url = "https://www.hikvision.com/content/dam/example/DS-3E0105P-E.pdf"
        fetch_url.return_value = (url, "text/html", b"<html><title>Challenge</title></html>")

        result = crawl_product((1, "Hikvision", "DS-3E0105P-E", "managed-switches", url))

        self.assertEqual(result["status"], "unsupported_content")

    def test_switch_ignores_document_heading_as_installation(self):
        specs = extract_specs(
            "Installation\nIndustrial PoE Switch | DH-PFS4207-4GT-DP\nManagement: Power consumption management",
            "managed-switches",
        )

        self.assertNotIn("installation", specs)
        self.assertNotIn("management_methods", specs)
