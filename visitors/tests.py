from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Visitor


class VisitorExitAccessTests(TestCase):
    def setUp(self):
        self.security_user = User.objects.create_user(
            username="security_exit",
            password="testpass123",
            role="security",
            phone="6666666666",
            is_approved=True,
        )
        self.resident_user = User.objects.create_user(
            username="resident_exit",
            password="testpass123",
            role="resident",
            phone="7777777777",
            is_approved=True,
        )
        self.visitor = Visitor.objects.create(
            name="Visitor One",
            phone="8888888888",
            flat_number="A-101",
            purpose="Delivery",
            security=self.security_user,
        )

    def test_get_visitor_exit_does_not_update_exit_time(self):
        self.client.force_login(self.security_user)

        response = self.client.get(reverse("visitor_exit", args=[self.visitor.id]))

        self.assertRedirects(response, reverse("visitor_list"))
        self.visitor.refresh_from_db()
        self.assertIsNone(self.visitor.exit_time)

    def test_resident_cannot_mark_visitor_exit(self):
        self.client.force_login(self.resident_user)

        response = self.client.post(reverse("visitor_exit", args=[self.visitor.id]))

        self.assertRedirects(response, reverse("dashboard"))
        self.visitor.refresh_from_db()
        self.assertIsNone(self.visitor.exit_time)

    def test_security_can_mark_visitor_exit(self):
        self.client.force_login(self.security_user)

        response = self.client.post(reverse("visitor_exit", args=[self.visitor.id]))

        self.assertRedirects(response, reverse("visitor_list"))
        self.visitor.refresh_from_db()
        self.assertIsNotNone(self.visitor.exit_time)
