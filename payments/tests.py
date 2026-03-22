from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Payment


class PaymentAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="resident_owner",
            password="testpass123",
            role="resident",
            phone="4444444444",
            is_approved=True,
        )
        self.other_user = User.objects.create_user(
            username="resident_other",
            password="testpass123",
            role="resident",
            phone="5555555555",
            is_approved=True,
        )
        self.payment = Payment.objects.create(
            resident=self.owner,
            month="March",
            year=2026,
            amount=Decimal("1500.00"),
            status="pending",
        )

    def test_get_pay_now_does_not_mark_payment_paid(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("pay_now", args=[self.payment.id]))

        self.assertRedirects(response, reverse("my_dues"))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")
        self.assertFalse(self.payment.transaction_id)

    def test_user_cannot_pay_another_users_payment(self):
        self.client.force_login(self.other_user)

        response = self.client.post(reverse("pay_now", args=[self.payment.id]))

        self.assertEqual(response.status_code, 404)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")

    def test_owner_can_pay_own_pending_payment(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse("pay_now", args=[self.payment.id]))

        self.assertRedirects(response, reverse("payment_history"))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "paid")
        self.assertTrue(self.payment.transaction_id)
