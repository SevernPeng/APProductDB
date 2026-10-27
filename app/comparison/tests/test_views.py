from datetime import date
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from catalog.models import (
    Brand,
    Category,
    ComparisonTemplate,
    Product,
    ProductSpec,
    SpecDefinition,
    TemplateField,
)
from comparison.models import ProductMatch


class ComparisonViewTests(TestCase):
    def setUp(self):
        viewer_group = Group.objects.get_or_create(name="Viewer")[0]
        user_model = get_user_model()
        self.viewer = user_model.objects.create_user(username="comparison-viewer")
        self.viewer.groups.add(viewer_group)
        self.no_role_user = user_model.objects.create_user(username="comparison-no-role")
        self.category = Category.objects.create(name="Access Point", slug="access-point")
        self.tp_link = Brand.objects.create(
            name="TP-Link", slug="tp-link", is_own_brand=True
        )
        self.ubiquiti = Brand.objects.create(name="Ubiquiti", slug="ubiquiti")
        self.ruijie = Brand.objects.create(name="Ruijie", slug="ruijie")
        self.definitions = {}
        definitions = (
            ("supported_bands", "Supported Wireless Bands", "Wireless", "text", ""),
            ("rate_2g_mbps", "2.4 GHz Max Rate", "Performance", "integer", "Mbps"),
            ("rate_5g_mbps", "5 GHz Max Rate", "Performance", "integer", "Mbps"),
            ("rate_6g_mbps", "6 GHz Max Rate", "Performance", "integer", "Mbps"),
            ("max_channel_width_mhz", "Max Channel Width", "Wireless", "integer", "MHz"),
            ("poe_output", "PoE Output", "Power", "text", ""),
        )
        for order, (code, name, group, data_type, unit) in enumerate(definitions, 1):
            self.definitions[code] = SpecDefinition.objects.create(
                code=code,
                display_name=name,
                group=group,
                data_type=data_type,
                unit=unit,
                is_core=True,
                display_order=order,
            )

        self.eap772 = self.create_product(
            self.tp_link, "EAP772", "https://example.com/eap772"
        )
        self.u7_pro = self.create_product(
            self.ubiquiti, "U7-Pro", "https://example.com/u7-pro"
        )
        self.rg_ap = self.create_product(
            self.ruijie, "RG-AP7136-R", "https://example.com/rg-ap7136-r"
        )
        self.add_text_spec(self.eap772, "supported_bands", "2.4 / 5 / 6 GHz")
        self.add_text_spec(self.u7_pro, "supported_bands", "2.4 / 5 / 6 GHz")
        self.add_text_spec(self.rg_ap, "supported_bands", "2.4 / 5 GHz")
        self.add_number_spec(self.eap772, "rate_2g_mbps", "574")
        self.add_number_spec(self.eap772, "rate_5g_mbps", "2882")
        self.add_number_spec(self.eap772, "rate_6g_mbps", "5764")
        self.add_number_spec(self.eap772, "max_channel_width_mhz", "320")
        self.add_number_spec(self.u7_pro, "rate_2g_mbps", "688")
        self.add_number_spec(self.u7_pro, "rate_5g_mbps", "2882")
        self.add_number_spec(self.u7_pro, "rate_6g_mbps", "5764")
        self.add_number_spec(self.rg_ap, "rate_2g_mbps", "0")
        self.add_number_spec(self.rg_ap, "rate_5g_mbps", "2882")
        self.add_text_spec(self.eap772, "poe_output", '=HYPERLINK("unsafe")')

        self.u7_match = ProductMatch.objects.create(
            our_product=self.eap772,
            competitor_product=self.u7_pro,
            match_type=ProductMatch.MatchType.DIRECT,
            status=ProductMatch.Status.CONFIRMED,
            match_score=95,
            reason="同级三频吸顶 AP",
            advantages="更高聚合速率",
            disadvantages="功耗依赖部署条件",
        )
        self.rg_match = ProductMatch.objects.create(
            our_product=self.eap772,
            competitor_product=self.rg_ap,
            match_type=ProductMatch.MatchType.PERFORMANCE,
            status=ProductMatch.Status.CONFIRMED,
        )

    def create_product(self, brand, model, official_url, **kwargs):
        return Product.objects.create(
            brand=brand,
            category=self.category,
            model=model,
            ap_type=Product.APType.CEILING,
            official_url=official_url,
            **kwargs,
        )

    def add_text_spec(self, product, code, value):
        return ProductSpec.objects.create(
            product=product,
            definition=self.definitions[code],
            value_text=value,
            source_url=product.official_url,
            verified_date=date(2026, 7, 18),
        )

    def add_number_spec(self, product, code, value):
        return ProductSpec.objects.create(
            product=product,
            definition=self.definitions[code],
            value_number=Decimal(value),
            source_url=product.official_url,
            verified_date=date(2026, 7, 18),
        )

    def comparison_url(self, *products, **options):
        query = "&".join(f"products={product.pk}" for product in products)
        for name, value in options.items():
            query += f"&{name}={value}"
        return reverse("comparison:compare") + "?" + query

    def test_pages_require_login_and_allow_every_account(self):
        urls = (
            reverse("comparison:benchmark"),
            reverse("comparison:compare"),
            self.comparison_url(self.eap772, self.u7_pro),
        )
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.no_role_user)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.viewer)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_benchmark_defaults_to_eap772_and_links_three_product_comparison(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("comparison:benchmark"))
        self.assertContains(response, "EAP772")
        self.assertContains(response, "U7-Pro")
        self.assertContains(response, "RG-AP7136-R")
        self.assertContains(response, "同级三频吸顶 AP")
        self.assertContains(response, "Compare All")
        self.assertContains(response, f"products={self.eap772.pk}")
        self.assertContains(response, f"products={self.u7_pro.pk}")
        self.assertContains(response, f"products={self.rg_ap.pk}")

    def test_benchmark_uses_normalized_fuzzy_search_instead_of_full_dropdown(self):
        outdoor = self.create_product(
            self.tp_link,
            "EAP772-Outdoor",
            "https://example.com/eap772-outdoor",
        )
        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("comparison:benchmark"), {"q": "eap 772-out"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, outdoor.model)
        self.assertContains(response, "1 models")
        self.assertNotContains(response, '<select class="form-select"')
        self.assertNotContains(response, "U7-Pro")

    def test_view_benchmarks_hides_search_results_and_shows_selected_product(self):
        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("comparison:benchmark"),
            {"q": "EAP772", "product": self.eap772.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["show_search_results"])
        self.assertEqual(response.context["selected_product"], self.eap772)
        self.assertNotContains(response, "Search Results")
        self.assertContains(response, "U7-Pro")
        self.assertContains(response, "View Product")

    def test_compare_displays_two_to_four_products_and_missing_states(self):
        self.client.force_login(self.viewer)
        response = self.client.get(
            self.comparison_url(self.eap772, self.u7_pro, self.rg_ap)
        )
        self.assertContains(response, "TP-Link")
        self.assertContains(response, "U7-Pro")
        self.assertContains(response, "RG-AP7136-R")
        self.assertContains(response, "0 Mbps")
        self.assertContains(response, "Not Applicable")
        self.assertContains(response, "Not Published")
        self.assertContains(response, "Unknown")
        self.assertNotContains(response, "Aggregate Rate")

    def test_comparison_derives_streams_and_rates_from_workbook(self):
        from comparison.services import build_comparison_rows, load_comparison_products

        streams = SpecDefinition.objects.create(code="total_spatial_streams",
            display_name="Total Spatial Streams", data_type="integer", group="Wireless", is_core=True)
        ProductSpec.objects.create(product=self.eap772, definition=streams, value_status="unknown")
        for code, label, text in (
            ("matrix-test-009", "Antenna", "• 2.4 GHz: 2× 4.0 dBi\n• 5 GHz: 4× 5.0 dBi\n• 6 GHz: 2× 5.0 dBi"),
            ("matrix-test-015", "Signal Rate", "• 6 GHz: 5.765 Gbps\n• 5 GHz: 8,648 Mbps\n• 2.4 GHz: 688 Mbps"),
        ):
            definition = SpecDefinition.objects.create(code=code, display_name=label,
                data_type="text", group="Wireless", is_core=False)
            ProductSpec.objects.create(product=self.eap772, definition=definition, value_text=text,
                source_url="https://example.com/workbook")
        self.eap772.specs.filter(definition__code__startswith="rate_").update(
            value_status="unknown", value_number=None)

        def rows():
            return {r["code"]: r for r in build_comparison_rows(
                load_comparison_products([self.eap772.pk, self.u7_pro.pk]))}

        result = rows()
        self.assertEqual(result["total_spatial_streams"]["values"][0]["display"], "8")
        self.assertEqual(result["rate_5g_mbps"]["values"][0]["display"], "8648 Mbps")
        self.assertNotIn("aggregate_rate_mbps", result)
        self.assertEqual(result["rate_6g_mbps"]["values"][0]["source_url"], "https://example.com/workbook")
        # Published MIMO takes precedence over antenna counts for that radio.
        mimo = SpecDefinition.objects.create(code="mimo_5g", display_name="5 GHz MIMO", data_type="text")
        ProductSpec.objects.create(product=self.eap772, definition=mimo, value_text="4×4:3 MIMO")
        self.assertEqual(rows()["total_spatial_streams"]["values"][0]["display"], "7")
        # Partial radio data must not be displayed as a complete total or as zero.
        self.eap772.specs.filter(definition__code="matrix-test-015").update(value_text="5 GHz: 8648 Mbps")
        self.assertNotIn("aggregate_rate_mbps", rows())

    def test_wireless_functions_resolve_mesh_and_fast_roaming(self):
        from comparison.services import build_comparison_rows, load_comparison_products

        for code, name, kind in (("mesh_support", "Mesh Support", "boolean"),
                                  ("fast_roaming", "Fast Roaming", "text")):
            definition = SpecDefinition.objects.create(code=code, display_name=name,
                data_type=kind, group="Management", is_core=True)
            ProductSpec.objects.create(product=self.eap772, definition=definition, value_status="unknown")
        functions = SpecDefinition.objects.create(code="matrix-wifi-016", display_name="Wireless Functions",
            data_type="text", group="Wireless", is_core=False)
        spec = ProductSpec.objects.create(product=self.eap772, definition=functions,
            value_text="• Mesh\n• 802.11 k/v/r", source_url="https://example.com/functions")

        def values():
            return {r["code"]: r["values"][0] for r in build_comparison_rows(
                load_comparison_products([self.eap772.pk, self.u7_pro.pk]))}

        result = values()
        self.assertEqual(result["mesh_support"]["display"], "Yes")
        self.assertEqual(result["fast_roaming"], {"display": "802.11r", "source_url": spec.source_url})
        for text, expected_mesh, expected_roaming in (
            ("802.11k/v", "Unknown", "Unknown"),
            ("Mesh: Not supported\n802.11r: Not supported", "No", "No"),
            ("Mesh\n802.11k / 802.11v / 802.11r", "Yes", "802.11r"),
        ):
            spec.value_text = text
            spec.save()
            result = values()
            self.assertEqual(result["mesh_support"]["display"], expected_mesh)
            self.assertEqual(result["fast_roaming"]["display"], expected_roaming)

    def test_compare_product_selectors_are_searchable_autocomplete_fields(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.comparison_url(self.eap772, self.u7_pro))
        self.assertContains(response, 'data-product-autocomplete')
        self.assertContains(response, 'type="search"')
        self.assertContains(response, 'name="products"')
        self.assertContains(response, f'data-value="{self.eap772.pk}"')
        self.assertNotContains(response, '<select class="form-select" id="compare-product-')

    def test_optional_selector_prioritizes_unselected_benchmark_products(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.comparison_url(self.eap772, self.u7_pro))

        optional_slot = response.context["selector_slots"][2]
        self.assertEqual(optional_slot["options"][0], self.rg_ap)
        self.assertTrue(optional_slot["options"][0].is_benchmark_suggestion)
        self.assertNotIn(self.eap772, optional_slot["options"])
        self.assertNotIn(self.u7_pro, optional_slot["options"])
        self.assertContains(response, ">Benchmark</span>", html=False)

    def test_compare_rejects_invalid_counts_and_unpublished_product(self):
        hidden = self.create_product(
            self.ubiquiti,
            "U7-HIDDEN",
            "https://example.com/hidden",
            is_published=False,
        )
        extra_one = self.create_product(self.ubiquiti, "U7-ONE", "")
        extra_two = self.create_product(self.ubiquiti, "U7-TWO", "")
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(self.comparison_url(self.eap772)).status_code, 400)
        self.assertEqual(
            self.client.get(
                self.comparison_url(
                    self.eap772,
                    self.u7_pro,
                    self.rg_ap,
                    extra_one,
                    extra_two,
                )
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.get(self.comparison_url(self.eap772, hidden)).status_code,
            400,
        )

    def test_compare_rejects_products_from_different_categories(self):
        switch_category = Category.objects.create(
            name="Managed",
            slug="managed-switches",
        )
        switch = Product.objects.create(
            brand=self.tp_link,
            category=switch_category,
            model="SG3428X",
        )
        self.client.force_login(self.viewer)

        response = self.client.get(self.comparison_url(self.eap772, switch))

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Only products of the same type can be compared", status_code=400)

    def test_only_differences_hides_equal_rows_and_sources_are_optional(self):
        self.client.force_login(self.viewer)
        difference_response = self.client.get(
            self.comparison_url(
                self.eap772, self.u7_pro, self.rg_ap, differences="1"
            )
        )
        self.assertNotContains(difference_response, "Wi-Fi Standard")
        self.assertContains(difference_response, "Supported Wireless Bands")
        without_sources = self.client.get(
            self.comparison_url(self.eap772, self.u7_pro)
        )
        self.assertNotContains(without_sources, ">Official source</a>", html=False)
        with_sources = self.client.get(
            self.comparison_url(self.eap772, self.u7_pro, sources="1")
        )
        self.assertContains(with_sources, ">Official source</a>", html=False)

    def test_compare_extended_toggle_controls_p2_rows(self):
        template = ComparisonTemplate.objects.create(
            category=self.category,
            form_factor=Product.APType.CEILING,
            name="Comparison priorities",
        )
        TemplateField.objects.create(
            template=template,
            spec_definition=self.definitions["supported_bands"],
            priority=TemplateField.Priority.P0,
            display_group="Wireless",
            display_order=10,
        )
        TemplateField.objects.create(
            template=template,
            spec_definition=self.definitions["poe_output"],
            priority=TemplateField.Priority.P2,
            display_group="Power",
            display_order=20,
        )
        self.client.force_login(self.viewer)

        default_response = self.client.get(
            self.comparison_url(self.eap772, self.u7_pro)
        )
        extended_response = self.client.get(
            self.comparison_url(self.eap772, self.u7_pro, extended="1")
        )

        self.assertNotContains(default_response, "PoE Output")
        self.assertContains(extended_response, "PoE Output")
        self.assertContains(extended_response, "HARDWARE FEATURES")
        self.assertNotContains(extended_response, "P2 ·")
        self.assertContains(extended_response, 'id="include-extended"')

    def test_competitor_first_still_uses_tp_link_template(self):
        vendor_only = SpecDefinition.objects.create(
            code="vendor_only",
            display_name="Vendor-only Field",
            group="Wireless",
            data_type="text",
        )
        tp_link_template = ComparisonTemplate.objects.create(
            category=self.category,
            form_factor=Product.APType.CEILING,
            name="TP-Link ceiling template",
        )
        competitor_template = ComparisonTemplate.objects.create(
            category=self.category,
            form_factor=Product.APType.OUTDOOR,
            name="Competitor product-type template",
        )
        TemplateField.objects.create(
            template=tp_link_template,
            spec_definition=self.definitions["supported_bands"],
            display_order=10,
        )
        TemplateField.objects.create(
            template=competitor_template,
            spec_definition=vendor_only,
            display_order=10,
        )
        self.u7_pro.ap_type = Product.APType.OUTDOOR
        self.u7_pro.save()
        ProductSpec.objects.create(
            product=self.u7_pro,
            definition=vendor_only,
            value_text="Must stay outside the comparison template",
        )
        self.client.force_login(self.viewer)

        response = self.client.get(
            self.comparison_url(self.u7_pro, self.eap772, extended="1")
        )

        self.assertContains(response, "Supported Wireless Bands")
        self.assertNotContains(response, "Vendor-only Field")
        self.assertNotContains(response, "Must stay outside the comparison template")

    def test_imported_tp_link_layout_excludes_bridge_fields_and_keeps_management_rows(self):
        bridge = SpecDefinition.objects.create(
            code="bridge_modes",
            display_name="Bridge / Operating Modes",
            group="Wireless",
            data_type="text",
        )
        polluted_template = ComparisonTemplate.objects.create(
            category=self.category,
            form_factor=Product.APType.CEILING,
            name="Polluted generic ceiling template",
        )
        TemplateField.objects.create(
            template=polluted_template,
            spec_definition=bridge,
            display_order=10,
        )
        ProductSpec.objects.create(
            product=self.eap772,
            definition=bridge,
            value_text="Must not define the product layout",
        )
        interface = SpecDefinition.objects.create(
            code="ethernet_interfaces",
            display_name="Ethernet Interfaces",
            group="Interfaces",
            data_type="text",
        )
        anchor_interface = SpecDefinition.objects.create(
            code="matrix-wifi-ceiling-interface",
            display_name="Interface",
            group="HARDWARE FEATURES",
            data_type="text",
            is_core=False,
        )
        ProductSpec.objects.create(
            product=self.eap772,
            definition=anchor_interface,
            value_text="1x 10G RJ45",
            source_note="Imported from ProductDB data 2.0.xlsx",
        )
        ProductSpec.objects.create(
            product=self.u7_pro,
            definition=interface,
            value_text="1x 2.5G RJ45",
        )
        for order, label in enumerate(
            ("Mobile APP", "Centralized Management", "SSH"),
            start=1,
        ):
            anchor_definition = SpecDefinition.objects.create(
                code=f"matrix-wifi-ceiling-{order:03d}",
                display_name=label,
                group="Management Features",
                data_type="text",
                is_core=False,
            )
            competitor_definition = SpecDefinition.objects.create(
                code=f"matrix-competitor-{order:03d}",
                display_name=label,
                group="Management Features",
                data_type="text",
                is_core=False,
            )
            ProductSpec.objects.create(
                product=self.eap772,
                definition=anchor_definition,
                value_text=f"TP-Link {label}",
                source_note="Imported from ProductDB data 2.0.xlsx",
            )
            ProductSpec.objects.create(
                product=self.u7_pro,
                definition=competitor_definition,
                value_text=f"Competitor {label}",
                source_note="Imported from competitor source",
            )

        from comparison.services import build_comparison_rows, load_comparison_products

        rows = build_comparison_rows(
            load_comparison_products([self.eap772.pk, self.u7_pro.pk]),
            include_extended=True,
        )
        names = [row["name"] for row in rows]
        self.assertEqual(
            [name for name in names if name in {"Mobile APP", "Centralized Management", "SSH"}],
            ["Mobile APP", "Centralized Management", "SSH"],
        )
        self.assertNotIn("Bridge / Operating Modes", names)
        interface_row = next(row for row in rows if row["name"] == "Interface")
        self.assertEqual(
            [value["display"] for value in interface_row["values"]],
            ["1x 10G RJ45", "1x 2.5G RJ45"],
        )
        ssh_row = next(row for row in rows if row["name"] == "SSH")
        self.assertEqual(
            [value["display"] for value in ssh_row["values"]],
            ["TP-Link SSH", "Competitor SSH"],
        )

    def test_export_contains_current_products_rows_and_sources(self):
        self.client.force_login(self.viewer)
        url = reverse("comparison:export") + "?" + "&".join(
            (
                f"products={self.eap772.pk}",
                f"products={self.u7_pro.pk}",
                "sources=1",
            )
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        workbook = load_workbook(BytesIO(response.content), read_only=True)
        worksheet = workbook["Comparison"]
        values = list(worksheet.values)
        self.assertEqual(values[0][0], "Specification")
        self.assertIn("TP-Link EAP772", values[0])
        self.assertIn("Ubiquiti U7-Pro Source", values[0])
        self.assertNotIn("Aggregate Rate", [row[0] for row in values])
        poe_row = next(row for row in values if row[0] == "PoE Output")
        self.assertEqual(poe_row[1], '\'=HYPERLINK("unsafe")')

    def test_product_detail_has_one_click_three_product_comparison(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("product-detail", args=[self.eap772.pk]))
        self.assertContains(response, "Compare All")
        self.assertContains(response, f"products={self.eap772.pk}")
        self.assertContains(response, f"products={self.u7_pro.pk}")
        self.assertContains(response, f"products={self.rg_ap.pk}")
