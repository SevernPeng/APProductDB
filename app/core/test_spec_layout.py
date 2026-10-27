from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Brand, Category, Product, ProductSpec, SpecDefinition
from comparison.models import ProductMatch


class CompetitorDetailLayoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Access Point", slug="access-point")
        own = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        other = Brand.objects.create(name="Ubiquiti", slug="ubiquiti")
        self.anchor = Product.objects.create(brand=own, category=category, model="EAP787", wifi_standard="Wi-Fi 7")
        self.competitor = Product.objects.create(brand=other, category=category, model="U7-Pro", wifi_standard="Wi-Fi 7")
        ProductMatch.objects.create(our_product=self.anchor, competitor_product=self.competitor,
                                   match_type="direct", status="confirmed")
        for order, (label, group) in enumerate((("Interface", "HARDWARE FEATURES"),
                ("Antenna", "HARDWARE FEATURES"), ("Button", "HARDWARE FEATURES"),
                ("Signal Rate", "WIRELESS FEATURES"), ("Wireless Functions", "WIRELESS FEATURES"))):
            definition = SpecDefinition.objects.create(code=f"matrix-reference-{order}",
                display_name=label, group=group, data_type="text", is_core=False, display_order=order)
            ProductSpec.objects.create(product=self.anchor, definition=definition, value_text="ANCHOR VALUE MUST NOT LEAK")
        for code, name, text in (("ethernet_interfaces", "Ethernet Interfaces", "1x 2.5G Port"),
                ("antenna_type", "Antenna Type", "2.4 GHz: 2× 4 dBi\n5 GHz: 2× 5 dBi"),
                ("supported_bands", "Supported Wireless Bands", "2.4/5 GHz"),
                ("fast_roaming", "Fast Roaming", "802.11r")):
            definition = SpecDefinition.objects.create(code=code, display_name=name, group="Wireless", data_type="text")
            ProductSpec.objects.create(product=self.competitor, definition=definition, value_text=text)
        for code, number in (("rate_2g_mbps", 688), ("rate_5g_mbps", 2882)):
            definition = SpecDefinition.objects.create(code=code, display_name=code, group="Performance", data_type="decimal", unit="Mbps")
            ProductSpec.objects.create(product=self.competitor, definition=definition, value_number=Decimal(number))
        self.client.force_login(get_user_model().objects.create_user(username="layout-viewer"))

    def test_competitor_uses_reference_labels_and_own_values(self):
        before = ProductSpec.objects.count()
        response = self.client.get(reverse("product-detail", args=[self.competitor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "ANCHOR VALUE MUST NOT LEAK")
        self.assertContains(response, "1x 2.5G Port")
        self.assertContains(response, "5 GHz: 2882 Mbps")
        self.assertNotContains(response, "Antenna Type")
        self.assertNotContains(response, "Aggregate Rate")
        groups = response.context["spec_groups"]
        self.assertEqual(groups[0]["name"], "HARDWARE FEATURES")
        self.assertEqual([r["display_name"] for r in groups[0]["rows"]], ["Interface", "Antenna", "Button"])
        self.assertEqual(groups[0]["rows"][2]["display_value"], "Unknown")
        self.assertEqual(ProductSpec.objects.count(), before)

    def test_native_values_are_preserved_but_extra_fields_are_removed(self):
        for code, label, text in (("matrix-other-016", "Wireless Functions", "Mesh\n802.11k/v/r\nBeamforming"),
                                  ("vendor_extra", "Vendor Feature", "Competitor-specific capability")):
            definition = SpecDefinition.objects.create(code=code, display_name=label, group="WIRELESS FEATURES",
                                                       data_type="text", is_core=False)
            ProductSpec.objects.create(product=self.competitor, definition=definition, value_text=text)
        response = self.client.get(reverse("product-detail", args=[self.competitor.pk]))
        self.assertContains(response, "Beamforming")
        self.assertNotContains(response, "Competitor-specific capability")
        self.assertNotContains(response, "Vendor Feature")
        rows = [r for g in response.context["spec_groups"] for r in g["rows"]]
        self.assertEqual(sum(r["display_name"] == "Wireless Functions" for r in rows), 1)
        response = self.client.get(reverse("product-detail", args=[self.competitor.pk]) + "?edit=1")
        self.assertNotContains(response, "Vendor Feature")
        extra = ProductSpec.objects.get(product=self.competitor, definition__code="vendor_extra")
        self.assertNotIn(f"spec_{extra.pk}", response.context["edit_form"].fields)

    def test_browse_and_edit_fields_exactly_match_tp_link(self):
        from catalog.wireless import BAND_WIDTH_CODE
        definition, _ = SpecDefinition.objects.get_or_create(code=BAND_WIDTH_CODE,
            defaults={"display_name": "Band Width", "data_type": "integer", "unit": "MHz"})
        ProductSpec.objects.create(product=self.competitor, definition=definition, value_number=160)
        mimo = SpecDefinition.objects.create(code="mimo_2g", display_name="2.4 GHz MIMO", data_type="text")
        ProductSpec.objects.create(product=self.anchor, definition=mimo, value_text="4x4")
        own = self.client.get(reverse("product-detail", args=[self.anchor.pk]))
        expected = [(g["name"], [r["display_name"] for r in g["rows"]]) for g in own.context["spec_groups"]]
        for suffix in ("", "?edit=1", ""):
            response = self.client.get(reverse("product-detail", args=[self.competitor.pk]) + suffix)
            actual = [(g["name"], [r["display_name"] for r in g["rows"]]) for g in response.context["spec_groups"]]
            self.assertEqual(actual, expected)
            self.assertContains(response, "Band Width")
            if suffix:
                fields = [r.get("edit_item") for g in response.context["spec_groups"] for r in g["rows"]]
                self.assertTrue(all(fields))
            else:
                self.assertContains(response, "160 MHz")
        response = self.client.get(reverse("product-detail", args=[self.competitor.pk]) + "?edit=1")
        form = response.context["edit_form"]
        data = {name: form[name].value() if form[name].value() is not None else "" for name in form.fields}
        width = self.competitor.specs.get(definition=definition)
        data.update(edit_mode="1", action="save_product", product_ap_type="ceiling")
        data[f"spec_{width.pk}"] = "80"
        self.assertEqual(self.client.post(reverse("product-detail", args=[self.competitor.pk]), data).status_code, 302)
        self.assertContains(self.client.get(reverse("product-detail", args=[self.competitor.pk])), "80 MHz")

    def test_same_label_in_different_groups_has_separate_values_and_edit_fields(self):
        for index, (group, value) in enumerate((("VPN", "Supported"), ("PERFORMANCE", "125 Mbps"))):
            definition = SpecDefinition.objects.create(code=f"matrix-vpn-{index}", display_name="GRE",
                group=group, data_type="text", is_core=False)
            ProductSpec.objects.create(product=self.anchor, definition=definition, value_text="REFERENCE")
            ProductSpec.objects.create(product=self.competitor, definition=definition, value_text=value)
        response = self.client.get(reverse("product-detail", args=[self.competitor.pk]) + "?edit=1")
        rows = [r for g in response.context["spec_groups"] for r in g["rows"] if r["display_name"] == "GRE"]
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["display_value"] for r in rows], ["Supported", "125 Mbps"])
        self.assertNotEqual(rows[0]["edit_item"]["name"], rows[1]["edit_item"]["name"])

    def test_shared_fields_are_editable_and_persist_competitor_values(self):
        mobile = SpecDefinition.objects.create(code="matrix-reference-mobile", display_name="Mobile APP",
            group="MANAGEMENT", data_type="text", is_core=False)
        ProductSpec.objects.create(product=self.anchor, definition=mobile, value_text="Omada APP")
        url = reverse("product-detail", args=[self.competitor.pk])
        response = self.client.get(url + "?edit=1")
        self.assertEqual(response.status_code, 200)
        rows = {r["display_name"]: r for g in response.context["spec_groups"] for r in g["rows"]}
        for label in ("Interface", "Antenna", "Button", "Signal Rate", "Wireless Functions", "Mobile APP"):
            self.assertIsNotNone(rows[label].get("edit_item"), label)
        self.assertNotContains(response, "ANCHOR VALUE MUST NOT LEAK")
        self.assertNotContains(response, 'value="Omada APP"')
        form = response.context["edit_form"]
        self.assertIn("2882", str(rows["Signal Rate"]["edit_item"]["field"]))
        post = {name: form[name].value() if form[name].value() is not None else "" for name in form.fields}
        post.update(edit_mode="1", action="save_product", product_ap_type="ceiling")
        for label, value in (("Mobile APP", "UniFi"), ("Button", "Reset"), ("Signal Rate", "Custom rate")):
            post[rows[label]["edit_item"]["name"]] = value
        response = self.client.post(url, post)
        self.assertEqual(response.status_code, 302, response.context["edit_form"].errors if response.context else "")
        response = self.client.get(url)
        self.assertContains(response, "UniFi")
        self.assertContains(response, "Reset")
        self.assertContains(response, "Custom rate")
        self.assertContains(response, "1x 2.5G Port")
        self.assertEqual(ProductSpec.objects.get(product=self.anchor, definition=mobile).value_text, "Omada APP")

    def test_competitor_wifi_detection_cannot_add_a_row_outside_reference_layout(self):
        gateway = Category.objects.create(name="Gateway", slug="gateway")
        anchor = Product.objects.create(
            brand=self.anchor.brand,
            category=gateway,
            model="ER8411",
        )
        competitor = Product.objects.create(
            brand=self.competitor.brand,
            category=gateway,
            model="UDR",
            wifi_standard="Wi-Fi 6",
        )
        ProductMatch.objects.create(
            our_product=anchor,
            competitor_product=competitor,
            match_type="direct",
            status="confirmed",
        )
        width, _ = SpecDefinition.objects.get_or_create(
            code="max_channel_width_mhz",
            defaults={
                "display_name": "Band Width",
                "group": "Wireless",
                "data_type": "integer",
                "unit": "MHz",
            },
        )
        ProductSpec.objects.create(
            product=competitor,
            definition=width,
            value_number=160,
        )

        from core.product_spec_layout import competitor_detail_rows
        from core.standard_spec_layout import standard_detail_rows

        expected = [
            (row["display_group"], row["display_name"])
            for row in standard_detail_rows(anchor)
        ]
        actual = [
            (row["display_group"], row["display_name"])
            for row in competitor_detail_rows(competitor, standard_detail_rows(competitor))
        ]
        self.assertEqual(actual, expected)
        self.assertNotIn(("WIRELESS FEATURES", "Band Width"), actual)
