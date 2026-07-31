from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="viewer", password="a-strong-test-password"
        )
        self.user.groups.add(Group.objects.get_or_create(name="Viewer")[0])

    def test_login_page_has_registration_link(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "登录")
        self.assertContains(response, "注册")

    def test_successful_login_redirects_to_home(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": "a-strong-test-password"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_logout_requires_post_and_redirects_to_login(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))


class GroupInitializationTests(TestCase):
    def test_required_groups_exist(self):
        self.assertTrue(Group.objects.filter(name="Viewer").exists())
        self.assertTrue(Group.objects.filter(name="Contributor").exists())


class AccountSystemTests(TestCase):
    def test_root_account_is_seeded_with_expected_role_and_password(self):
        root = get_user_model().objects.get(username="root")
        self.assertTrue(root.is_superuser)
        self.assertTrue(root.check_password("Nqt1_Ulk0"))
        self.assertEqual(root.account_profile.role, "root")

    def test_registration_requires_company_email_and_rejects_duplicates(self):
        url = reverse("accounts:register")
        response = self.client.post(
            url,
            {"email": "person@example.com", "password1": "Good-Test-Pass-928!", "password2": "Good-Test-Pass-928!"},
        )
        self.assertContains(response, "仅支持 @tp-link.com 公司邮箱")
        response = self.client.post(
            url,
            {"email": "Person@TP-LINK.COM", "password1": "Good-Test-Pass-928!", "password2": "Good-Test-Pass-928!"},
        )
        self.assertRedirects(response, reverse("home"))
        user = get_user_model().objects.get(username="person@tp-link.com")
        self.assertEqual(user.account_profile.role, "user")
        self.client.logout()
        response = self.client.post(
            url,
            {"email": "PERSON@tp-link.com", "password1": "Another-Test-Pass-837!", "password2": "Another-Test-Pass-837!"},
        )
        self.assertContains(response, "该邮箱已注册")
        self.assertEqual(get_user_model().objects.filter(email__iexact="person@tp-link.com").count(), 1)

    def test_company_email_login_is_case_insensitive(self):
        user = get_user_model().objects.create_user(
            username="person@tp-link.com", email="person@tp-link.com", password="Good-Test-Pass-928!"
        )
        from accounts.models import AccountProfile
        AccountProfile.objects.create(user=user, email=user.email, role="user")
        response = self.client.post(
            reverse("login"),
            {"username": "PERSON@TP-LINK.COM", "password": "Good-Test-Pass-928!"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_only_root_can_promote_and_demote_accounts(self):
        from accounts.models import AccountProfile
        user = get_user_model().objects.create_user(
            username="member@tp-link.com", email="member@tp-link.com"
        )
        profile = AccountProfile.objects.create(user=user, email=user.email, role="user")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("accounts:list")).status_code, 403)
        root = get_user_model().objects.get(username="root")
        self.client.force_login(root)
        self.client.post(reverse("accounts:update-role", args=[profile.pk]), {"role": "admin"})
        profile.refresh_from_db()
        self.assertEqual(profile.role, "admin")
        self.client.post(reverse("accounts:update-role", args=[profile.pk]), {"role": "user"})
        profile.refresh_from_db()
        self.assertEqual(profile.role, "user")
