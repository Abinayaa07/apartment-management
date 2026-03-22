from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import AssignPaymentForm
from .models import Payment
from django.contrib import messages
from django.views.decorators.http import require_POST
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics, permissions

from core.notifications import (
    send_new_due_notification,
    send_payment_success_notification,
)
from .serializers import PaymentSerializer


@login_required
def my_dues(request):
    payments = Payment.objects.filter(resident=request.user).order_by("-created_at")
    month = request.GET.get("month", "").strip()
    year = request.GET.get("year", "").strip()
    status = request.GET.get("status", "").strip()

    if month:
        payments = payments.filter(month__icontains=month)
    if year:
        payments = payments.filter(year=year)
    if status:
        payments = payments.filter(status=status)

    return render(
        request,
        "payments/my_dues.html",
        {
            "payments": payments,
            "filters": {"month": month, "year": year, "status": status},
            "status_choices": Payment.STATUS_CHOICES,
        }
    )

@login_required
def payment_history(request):
    payments = Payment.objects.filter(
        resident=request.user,
        status="paid"
    ).order_by("-created_at")
    month = request.GET.get("month", "").strip()
    year = request.GET.get("year", "").strip()
    transaction_id = request.GET.get("transaction_id", "").strip()

    if month:
        payments = payments.filter(month__icontains=month)
    if year:
        payments = payments.filter(year=year)
    if transaction_id:
        payments = payments.filter(transaction_id__icontains=transaction_id)

    return render(
        request,
        "payments/payment_history.html",
        {
            "payments": payments,
            "filters": {
                "month": month,
                "year": year,
                "transaction_id": transaction_id,
            },
        }
    )


@login_required
def manage_payments(request):
    if request.user.role not in ["staff", "admin"]:
        messages.error(request, "Only staff or admin can manage payments.")
        return redirect("dashboard")

    payments = Payment.objects.all().order_by("-created_at")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    month = request.GET.get("month", "").strip()
    year = request.GET.get("year", "").strip()

    if query:
        payments = payments.filter(
            Q(resident__username__icontains=query) |
            Q(transaction_id__icontains=query) |
            Q(month__icontains=query)
        )
    if status:
        payments = payments.filter(status=status)
    if month:
        payments = payments.filter(month__icontains=month)
    if year:
        payments = payments.filter(year=year)

    return render(
        request,
        "payments/manage_payments.html",
        {
            "payments": payments,
            "assign_form": AssignPaymentForm(),
            "status_choices": Payment.STATUS_CHOICES,
            "filters": {
                "q": query,
                "status": status,
                "month": month,
                "year": year,
            },
        }
    )


@login_required
def assign_payment(request):
    if request.user.role not in ["staff", "admin"]:
        messages.error(request, "Only staff or admin can assign payments.")
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("dashboard")

    form = AssignPaymentForm(request.POST)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.status = "pending"
        payment.payment_method = ""
        payment.transaction_id = ""
        payment.save()
        send_new_due_notification(request, payment)
        messages.success(request, "Payment due assigned successfully.")
    else:
        messages.error(request, "Please complete all payment fields correctly.")

    return redirect(request.POST.get("next") or "dashboard")

import uuid
from django.shortcuts import redirect, get_object_or_404


@login_required
def pay_now(request, payment_id):

    if request.method != "POST":
        return redirect("my_dues")

    payment = get_object_or_404(
        Payment,
        id=payment_id,
        resident=request.user,
        status="pending",
    )

    payment_method = request.POST.get("payment_method", "upi").strip().lower()
    if payment_method not in dict(Payment.PAYMENT_METHOD_CHOICES):
        messages.error(request, "Please choose a valid payment method.")
        return redirect("my_dues")

    payment.status = "paid"
    payment.payment_method = payment_method
    payment.transaction_id = str(uuid.uuid4())

    payment.save()
    send_payment_success_notification(request, request.user, payment, payment_method=payment.get_payment_method_display())

    return redirect("payment_history")


@login_required
def create_payment(request, payment_id):
    try:
        import razorpay
    except ImportError:
        messages.error(request, "Online payment is not configured yet.")
        return redirect("my_dues")

    payment = get_object_or_404(
        Payment,
        id=payment_id,
        resident=request.user,
        status="pending",
    )

    client = razorpay.Client(
        auth=("RAZORPAY_KEY", "RAZORPAY_SECRET")
    )

    order = client.order.create({
        "amount": int(payment.amount * 100),
        "currency": "INR",
        "payment_capture": "1"
    })

    context = {
        "payment": payment,
        "order_id": order["id"],
    }

    return render(request, "payments/pay.html", context)

@login_required
@require_POST
def payment_success(request):
    payment_id = request.POST.get("razorpay_payment_id")

    payment = get_object_or_404(
        Payment,
        id=request.POST.get("payment_id"),
        resident=request.user,
        status="pending",
    )

    payment.status = "paid"
    payment.transaction_id = payment_id
    payment.payment_method = "upi"
    payment.save()
    send_payment_success_notification(request, request.user, payment, payment_method=payment.get_payment_method_display())

    return redirect("payment_history")


@login_required
def update_payment(request, payment_id):
    if request.user.role not in ["staff", "admin"]:
        messages.error(request, "Only staff or admin can update payments.")
        return redirect("dashboard")

    payment = get_object_or_404(Payment, id=payment_id)

    if request.method == "POST":
        payment.status = request.POST.get("status", payment.status)
        payment.transaction_id = request.POST.get("transaction_id", payment.transaction_id)
        payment_method = request.POST.get("payment_method", payment.payment_method)
        if payment_method in dict(Payment.PAYMENT_METHOD_CHOICES):
            payment.payment_method = payment_method
        payment.save()
        messages.success(request, "Payment updated successfully.")
        return redirect("manage_payments")

    return render(
        request,
        "payments/update_payment.html",
        {
            "payment": payment,
            "status_choices": Payment.STATUS_CHOICES,
            "method_choices": Payment.PAYMENT_METHOD_CHOICES,
        }
    )


class PaymentListAPI(generics.ListAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ["staff", "admin"]:
            return Payment.objects.all().order_by("-created_at")
        return Payment.objects.filter(resident=user).order_by("-created_at")


class PaymentCreateAPI(generics.CreateAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role not in ["staff", "admin"]:
            raise PermissionDenied("Only staff or admin can create payments.")
        payment = serializer.save()
        send_new_due_notification(self.request, payment)


class PaymentUpdateAPI(generics.UpdateAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        if self.request.user.role in ["staff", "admin"]:
            return Payment.objects.all()
        return Payment.objects.filter(resident=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.role not in ["staff", "admin"]:
            raise PermissionDenied("Only staff or admin can update payments.")
        serializer.save()
