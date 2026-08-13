from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import AccountProfile
from audit.models import AuditLog
from catalog.models import Brand, Category, Product, ProductSpec, SpecDefinition
from changes.models import ChangeRequest
from changes.services import build_target_options, resolve_target
from changes.validators import MAX_ATTACHMENT_SIZE, validate_change_attachment
from comparison.models import ProductMatch


class ChangeWorkflowTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_override.enable()
        viewer_group = Group.objects.get_or_create(name="Viewer")[0]
        contributor_group = Group.objects.get_or_create(name="Contributor")[0]
        user_model = get_user_model()
        self.viewer = user_model.objects.create_user(username="change-viewer")
        self.viewer.groups.add(viewer_group)
        self.contributor = user_model.objects.create_user(username="change-contributor")
        self.contributor.groups.add(contributor_group)
        self.other_contributor = user_model.objects.create_user(username="change-other")
        self.other_contributor.groups.add(contributor_group)
        self.admin = user_model.objects.create_superuser(username="change-admin")
        self.category = Category.objects.create(name="Access Point", slug="access-point")
        self.tp_link = Brand.objects.create(
            name="TP-Link", slug="tp-link", is_own_brand=True
        )
        self.ubiquiti = Brand.objects.create(name="Ubiquiti", slug="ubiquiti")
        self.product = Product.objects.create(
            brand=self.tp_link,
            category=self.category,
            model="EAP772",
            ap_type=Product.APType.CEILING,
            notes="Original notes",
            official_url="https://example.com/eap772",
        )
        self.competitor = Product.objects.create(
            brand=self.ubiquiti,
            category=self.category,
            model="U7-Pro",
            ap_type=Product.APType.CEILING,
        )
        self.definition = SpecDefinition.objects.create(
            code="max_clients",
            display_name="Max Clients",
            group="Capacity",
            data_type=SpecDefinition.DataType.INTEGER,
            unit="",
            is_core=True,
        )
        self.spec = ProductSpec.objects.create(
            product=self.product,
            definition=self.definition,
            value_number=100,
            source_url="https://example.com/old",
        )
        self.match = ProductMatch.objects.create(
            our_product=self.product,
            competitor_product=self.competitor,
            match_type=ProductMatch.MatchType.DIRECT,
            status=ProductMatch.Status.CONFIRMED,
            reason="Original reason",
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_directory.cleanup()

    def create_spec_change(self, **overrides):
        values = {
            "request_type": ChangeRequest.RequestType.SPEC,
            "target_product": self.product,
            "target_spec": self.spec,
            "field_name": self.definition.code,
            "old_value": {"value_text": "", "value_number": "100"},
            "proposed_value": {"value_text": "", "value_number": "200"},
            "reason": "Official specification correction",
            "source_url": "https://example.com/new",
            "submitted_by": self.contributor,
        }
        values.update(overrides)
        return ChangeRequest.objects.create(**values)

    def test_all_authenticated_users_can_modify_and_only_owner_or_root_sees_history(self):
        suggest_url = reverse("changes:suggest", args=[self.product.pk])
        self.assertEqual(self.client.get(suggest_url).status_code, 302)
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(suggest_url).status_code, 200)
        self.client.force_login(self.contributor)
        self.assertEqual(self.client.get(suggest_url).status_code, 200)
        change = self.create_spec_change()
        self.client.force_login(self.other_contributor)
        self.assertEqual(
            self.client.get(reverse("changes:detail", args=[change.pk])).status_code,
            403,
        )
        root = get_user_model().objects.get(username="root")
        self.client.force_login(root)
        self.assertEqual(
            self.client.get(reverse("changes:detail", args=[change.pk])).status_code,
            200,
        )
        self.assertEqual(self.client.get("/reviews/").status_code, 404)

    def test_editable_fields_follow_product_category_and_actual_specs(self):
        secondary_definition = SpecDefinition.objects.create(
            code="secondary_feature",
            display_name="Secondary Feature",
            group="Features",
            data_type=SpecDefinition.DataType.TEXT,
            is_core=False,
            display_order=50,
        )
        secondary_spec = ProductSpec.objects.create(
            product=self.product,
            definition=secondary_definition,
            value_text="Supported",
        )
        inactive_definition = SpecDefinition.objects.create(
            code="inactive_feature",
            display_name="Inactive Feature",
            group="Features",
            data_type=SpecDefinition.DataType.TEXT,
            is_core=False,
            active=False,
        )
        inactive_spec = ProductSpec.objects.create(
            product=self.product,
            definition=inactive_definition,
            value_text="Legacy",
        )

        option_keys = {
            option["key"] for option in build_target_options(self.product)
        }
        self.assertIn("product:sku", option_keys)
        self.assertIn("product:datasheet_url", option_keys)
        self.assertIn("product:launch_date", option_keys)
        self.assertIn("product:ap_type", option_keys)
        self.assertIn(f"spec:{secondary_spec.pk}", option_keys)
        self.assertNotIn(f"spec:{inactive_spec.pk}", option_keys)
        self.assertIn(f"match:{self.match.pk}:reason", option_keys)
        self.assertIn(f"match:{self.match.pk}:__delete__", option_keys)
        self.assertEqual(
            resolve_target(self.product, f"spec:{secondary_spec.pk}")["target"],
            secondary_spec,
        )
        self.assertEqual(
            resolve_target(
                self.product,
                f"match:{self.match.pk}:reason",
            )["target"],
            self.match,
        )

        switch_category = Category.objects.create(
            name="Managed Switch",
            slug="managed-switches",
        )
        switch = Product.objects.create(
            brand=self.tp_link,
            category=switch_category,
            model="SG2008",
        )
        switch_keys = {
            option["key"] for option in build_target_options(switch)
        }
        self.assertNotIn("product:ap_type", switch_keys)
        self.assertNotIn("product:wifi_standard", switch_keys)
        with self.assertRaises(ValidationError):
            resolve_target(switch, "product:ap_type")

        self.client.force_login(self.contributor)
        response = self.client.get(
            reverse("changes:suggest", args=[self.product.pk])
        )
        self.assertContains(response, "<optgroup", html=False)
        self.assertContains(response, "Secondary Feature")

    def test_non_core_boolean_spec_can_be_changed(self):
        definition = SpecDefinition.objects.create(
            code="mesh_support",
            display_name="Mesh Support",
            group="Features",
            data_type=SpecDefinition.DataType.BOOLEAN,
            is_core=False,
        )
        spec = ProductSpec.objects.create(
            product=self.product,
            definition=definition,
            value_boolean=False,
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "target": f"spec:{spec.pk}",
                "proposed_value": "Yes",
                "reason": "Official correction",
                "source_url": "https://example.com/mesh",
            },
        )
        self.assertEqual(response.status_code, 302)
        spec.refresh_from_db()
        change = ChangeRequest.objects.get(target_spec=spec)
        self.assertTrue(spec.value_boolean)
        self.assertEqual(change.old_value, {"value_boolean": False})
        self.assertEqual(change.proposed_value, {"value_boolean": True})

    def test_missing_category_specs_are_created_as_editable_unknown_fields(self):
        category_definition = SpecDefinition.objects.create(
            code="poe_budget",
            display_name="PoE Budget",
            group="Power",
            category=self.category,
            data_type=SpecDefinition.DataType.INTEGER,
            unit="W",
            is_core=False,
        )
        other_category = Category.objects.create(
            name="Gateway",
            slug="gateway",
        )
        unrelated_definition = SpecDefinition.objects.create(
            code="wan_ports",
            display_name="WAN Ports",
            group="Interfaces",
            category=other_category,
            data_type=SpecDefinition.DataType.INTEGER,
        )
        self.assertFalse(self.competitor.specs.exists())

        self.client.force_login(self.contributor)
        response = self.client.get(
            reverse("changes:suggest", args=[self.competitor.pk])
        )
        self.assertEqual(response.status_code, 200)
        placeholder = ProductSpec.objects.get(
            product=self.competitor,
            definition=category_definition,
        )
        self.assertEqual(
            placeholder.value_status,
            ProductSpec.ValueStatus.UNKNOWN,
        )
        self.assertContains(response, f'value="spec:{placeholder.pk}"')
        self.assertFalse(
            ProductSpec.objects.filter(
                product=self.competitor,
                definition=unrelated_definition,
            ).exists()
        )

    def test_competitor_page_can_modify_and_delete_incoming_match(self):
        option_keys = {
            option["key"] for option in build_target_options(self.competitor)
        }
        self.assertIn(f"match:{self.match.pk}:reason", option_keys)
        self.assertIn(f"match:{self.match.pk}:__delete__", option_keys)
        self.assertEqual(
            resolve_target(
                self.competitor,
                f"match:{self.match.pk}:reason",
            )["target"],
            self.match,
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("changes:suggest", args=[self.competitor.pk]),
            {
                "target": f"match:{self.match.pk}:__delete__",
                "reason": "Remove incorrect reverse association",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, ProductMatch.Status.REJECTED)

    def test_admin_can_add_and_delete_competitor_relationships(self):
        second_competitor = Product.objects.create(
            brand=self.ubiquiti,
            category=self.category,
            model="U7-Pro-XG",
            ap_type=Product.APType.CEILING,
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "action": "add_match",
                "competitor_product": second_competitor.pk,
                "match_type": ProductMatch.MatchType.PERFORMANCE,
                "match_level": ProductMatch.MatchLevel.SECONDARY,
                "rank": 3,
                "match_score": 88,
                "confidence": 90,
                "relation_reason": "Comparable Wi-Fi 7 model",
                "source_url": "https://example.com/comparison",
                "request_reason": "Add the missing competitor",
            },
        )
        self.assertEqual(response.status_code, 302)
        added = ProductMatch.objects.get(
            our_product=self.product,
            competitor_product=second_competitor,
        )
        self.assertEqual(added.match_type, ProductMatch.MatchType.PERFORMANCE)
        self.assertEqual(added.match_level, ProductMatch.MatchLevel.SECONDARY)
        self.assertEqual(added.match_score, 88)
        self.assertEqual(added.status, ProductMatch.Status.CONFIRMED)
        add_change = ChangeRequest.objects.get(field_name="__add__")
        self.assertEqual(add_change.status, ChangeRequest.Status.APPROVED)

        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "target": f"match:{added.pk}:__delete__",
                "reason": "This model is no longer a valid competitor",
            },
        )
        self.assertEqual(response.status_code, 302)
        added.refresh_from_db()
        self.assertEqual(added.status, ProductMatch.Status.REJECTED)
        delete_change = ChangeRequest.objects.get(
            target_match=added,
            field_name="__delete__",
        )
        self.assertEqual(delete_change.status, ChangeRequest.Status.APPROVED)

    def test_user_match_add_is_applied_immediately(self):
        second_competitor = Product.objects.create(
            brand=self.ubiquiti,
            category=self.category,
            model="U7-Lite",
            ap_type=Product.APType.CEILING,
        )
        self.client.force_login(self.contributor)
        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "action": "add_match",
                "competitor_product": second_competitor.pk,
                "match_type": ProductMatch.MatchType.DIRECT,
                "match_level": ProductMatch.MatchLevel.CORE,
                "relation_reason": "Same market segment",
                "source_url": "https://example.com/u7-lite",
                "request_reason": "Missing competitor",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ProductMatch.objects.filter(
                our_product=self.product,
                competitor_product=second_competitor,
            ).exists()
        )
        change = ChangeRequest.objects.get(field_name="__add__")
        self.assertEqual(change.status, ChangeRequest.Status.APPROVED)
        self.assertEqual(change.reviewed_by, self.contributor)
        self.assertTrue(
            ProductMatch.objects.filter(
                our_product=self.product,
                competitor_product=second_competitor,
                status=ProductMatch.Status.CONFIRMED,
            ).exists()
        )

    def test_spec_submission_requires_evidence_and_rejects_same_value(self):
        self.client.force_login(self.contributor)
        url = reverse("changes:suggest", args=[self.product.pk])
        response = self.client.post(
            url,
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "200",
                "reason": "Correction",
            },
        )
        self.assertContains(response, "Provide an official source URL or evidence attachment")
        response = self.client.post(
            url,
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "100",
                "reason": "Correction",
                "source_url": "https://example.com/source",
            },
        )
        self.assertContains(response, "The proposed value must differ from the current value")
        self.assertFalse(ChangeRequest.objects.exists())

    def test_valid_submission_uses_server_side_actor_applies_and_audits(self):
        self.client.force_login(self.contributor)
        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "200",
                "reason": "Correction",
                "source_url": "https://example.com/new",
                "submitted_by": self.admin.pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        change = ChangeRequest.objects.get()
        self.assertEqual(change.submitted_by, self.contributor)
        self.assertEqual(change.old_value["value_number"], "100")
        self.spec.refresh_from_db()
        self.assertEqual(self.spec.value_number, 200)
        change.refresh_from_db()
        self.assertEqual(change.status, ChangeRequest.Status.APPROVED)
        audit = AuditLog.objects.get(actor=self.contributor, action="change.applied")
        self.assertEqual(audit.before_data["value_number"], "100")
        self.assertEqual(audit.after_data["value_number"], "200")

    def test_non_root_account_is_user_and_change_is_applied_without_review(self):
        user = get_user_model().objects.create_user(
            username="editor@tp-link.com", email="editor@tp-link.com", password="secret"
        )
        self.assertEqual(user.account_profile.role, AccountProfile.Role.USER)
        self.assertFalse(user.is_superuser)
        self.client.force_login(user)
        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "250",
                "reason": "User correction",
                "source_url": "https://example.com/user-source",
            },
        )
        self.assertEqual(response.status_code, 302)
        change = ChangeRequest.objects.get(submitted_by=user)
        change.refresh_from_db()
        self.spec.refresh_from_db()
        self.assertEqual(change.status, ChangeRequest.Status.APPROVED)
        self.assertEqual(change.reviewed_by, user)
        self.assertEqual(self.spec.value_number, 250)
        self.assertTrue(AuditLog.objects.filter(actor=user, action="change.applied").exists())

    def test_product_page_editor_updates_multiple_fields_with_audit_history(self):
        self.client.force_login(self.contributor)
        response = self.client.get(
            reverse("changes:edit-product", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit page content")
        self.assertContains(response, 'name="product_notes"')
        self.assertContains(response, f'name="spec_{self.spec.pk}"')
        integer_input = str(response.context["form"][f"spec_{self.spec.pk}"])
        self.assertIn('step="1"', integer_input)
        self.assertIn('value="100"', integer_input)
        self.assertNotIn('value="100.000"', integer_input)

        post_data = {
            name: (
                response.context["form"][name].value()
                if response.context["form"][name].value() is not None
                else ""
            )
            for name in response.context["form"].fields
        }
        post_data["product_notes"] = "Updated on the product page"
        post_data[f"spec_{self.spec.pk}"] = "275"
        response = self.client.post(
            reverse("changes:edit-product", args=[self.product.pk]),
            post_data,
        )

        self.assertRedirects(response, reverse("product-detail", args=[self.product.pk]))
        self.product.refresh_from_db()
        self.spec.refresh_from_db()
        self.assertEqual(self.product.notes, "Updated on the product page")
        self.assertEqual(self.spec.value_number, 275)
        self.assertEqual(
            ChangeRequest.objects.filter(submitted_by=self.contributor).count(),
            2,
        )
        self.assertEqual(
            AuditLog.objects.filter(actor=self.contributor, action="change.applied").count(),
            2,
        )

    def test_product_page_editor_rejects_decimals_for_integer_specs(self):
        self.client.force_login(self.contributor)
        url = reverse("changes:edit-product", args=[self.product.pk])
        response = self.client.get(url)
        post_data = {
            name: (
                response.context["form"][name].value()
                if response.context["form"][name].value() is not None
                else ""
            )
            for name in response.context["form"].fields
        }
        post_data[f"spec_{self.spec.pk}"] = "275.5"

        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a whole number")
        self.spec.refresh_from_db()
        self.assertEqual(self.spec.value_number, 100)
        self.assertFalse(ChangeRequest.objects.exists())

    def test_attachment_type_content_size_and_object_access_are_protected(self):
        self.client.force_login(self.contributor)
        url = reverse("changes:suggest", args=[self.product.pk])
        invalid = SimpleUploadedFile("proof.pdf", b"not a pdf")
        response = self.client.post(
            url,
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "200",
                "reason": "Correction",
                "attachment": invalid,
            },
        )
        self.assertContains(response, "The attachment content does not match its file extension")

        valid_content = b"%PDF-1.7\nproof"
        valid = SimpleUploadedFile("proof.pdf", valid_content)
        response = self.client.post(
            url,
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "200",
                "reason": "Correction",
                "attachment": valid,
            },
        )
        self.assertEqual(response.status_code, 302)
        change = ChangeRequest.objects.get()
        self.assertNotIn("proof.pdf", change.attachment.name)
        download_url = reverse("changes:attachment", args=[change.pk])
        response = self.client.get(download_url)
        self.assertEqual(b"".join(response.streaming_content), valid_content)
        response.close()
        self.client.force_login(self.other_contributor)
        self.assertEqual(self.client.get(download_url).status_code, 403)
        change.refresh_from_db()
        self.assertEqual(change.status, ChangeRequest.Status.APPROVED)

        oversized = BytesIO(b"%PDF-1.7")
        oversized.name = "large.pdf"
        oversized.size = MAX_ATTACHMENT_SIZE + 1
        with self.assertRaises(ValidationError):
            validate_change_attachment(oversized)
