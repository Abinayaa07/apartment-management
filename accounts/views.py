from datetime import timedelta
import json

from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegisterForm
from django.contrib import messages
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.notifications import (
    send_login_notification,
    send_registration_notification,
    send_user_notification,
)
from .chatbot import get_faq_answer


def home(request):
    return render(request, "accounts/home.html")


@csrf_exempt
@require_POST
def faq_chat(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {
                "answer": "I could not read that question. Please try again.",
                "matched": False,
            },
            status=400,
        )

    result = get_faq_answer(payload.get("message", ""))
    return JsonResponse(result)


def register(request):

    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save(commit=False)

            # Residents require approval
            if user.role == "resident":
                user.is_approved = False
            else:
                user.is_approved = True

            user.save()
            send_registration_notification(request, user)

            if user.role == "resident":
                messages.success(request, "Account created. Your documents are pending admin approval.")
            else:
                messages.success(request, "Account created successfully.")

            return redirect('login')

    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})



from django.contrib.auth import authenticate, login
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


def user_login(request):

    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:

            if not user.is_approved:
                messages.error(request, "Account not approved by admin.")
                return redirect('login')

            login(request, user)
            send_login_notification(request, user)

            return redirect('dashboard')

        else:
            messages.error(request, "Invalid credentials")

    return render(request, "accounts/login.html")

from django.contrib.auth import logout
from django.utils import timezone


def user_logout(request):
    logout(request)
    return redirect('login')

from notices.models import Notice
from payments.forms import AssignPaymentForm
from payments.models import Payment
from tickets.models import Ticket
from visitors.models import Visitor


@login_required
def dashboard(request):
    role = request.user.role
    stats = []
    quick_links = []
    analytics = {}
    pending_residents = []
    users_by_role = []
    assign_payment_form = None

    if role == "resident":
        template = "accounts/resident_dashboard.html"
        stats = [
            {"label": "My Tickets", "value": request.user.tickets.count(), "tone": "primary"},
            {"label": "Open Tickets", "value": request.user.tickets.exclude(status="closed").count(), "tone": "warning"},
            {"label": "Pending Dues", "value": Payment.objects.filter(resident=request.user, status="pending").count(), "tone": "success"},
            {"label": "Notices", "value": Notice.objects.count(), "tone": "info"},
        ]
        quick_links = [
            {"title": "Pay Maintenance Dues", "subtitle": "View and clear pending maintenance charges.", "href": "/payments/dues/", "tone": "success"},
            {"title": "Create Ticket", "subtitle": "Raise a maintenance or support issue.", "href": "/tickets/create/", "tone": "primary"},
            {"title": "Payment History", "subtitle": "Check completed dues and receipts.", "href": "/payments/history/", "tone": "warning"},
        ]

    elif role == "security":
        template = "accounts/security_dashboard.html"
        stats = [
            {"label": "Visitors Today", "value": Visitor.objects.filter(entry_time__date=timezone.now().date()).count(), "tone": "success"},
            {"label": "Inside Society", "value": Visitor.objects.filter(exit_time__isnull=True).count(), "tone": "warning"},
            {"label": "Notice Board", "value": Notice.objects.count(), "tone": "info"},
            {"label": "Total Logs", "value": Visitor.objects.count(), "tone": "primary"},
        ]
        quick_links = [
            {"title": "Add Visitor Entry", "subtitle": "Log a new visitor at the gate.", "href": "/visitors/add/", "tone": "success"},
            {"title": "Visitor Log", "subtitle": "Review entries and mark exits.", "href": "/visitors/list/", "tone": "primary"},
            {"title": "View Notices", "subtitle": "Check latest staff and admin notices.", "href": "/notices/list/", "tone": "info"},
        ]

    elif role == "staff":
        template = "accounts/staff_dashboard.html"
        assign_payment_form = AssignPaymentForm()
        stats = [
            {"label": "All Tickets", "value": Ticket.objects.count(), "tone": "primary"},
            {"label": "Open Tickets", "value": Ticket.objects.exclude(status="closed").count(), "tone": "warning"},
            {"label": "Pending Payments", "value": Payment.objects.filter(status="pending").count(), "tone": "success"},
            {"label": "Active Notices", "value": Notice.objects.count(), "tone": "info"},
        ]
        quick_links = [
            {"title": "Manage Tickets", "subtitle": "Review and update society issues.", "href": "/tickets/all/", "tone": "primary"},
            {"title": "Create Notice", "subtitle": "Publish an announcement for residents.", "href": "/notices/create/", "tone": "info"},
            {"title": "Assign Payment", "subtitle": "Create a new due for a resident.", "href": "#assign-payment", "tone": "warning"},
            {"title": "Manage Payments", "subtitle": "Track pending and completed dues.", "href": "/payments/manage/", "tone": "warning"},
        ]

    else:
        template = "accounts/admin_dashboard.html"
        assign_payment_form = AssignPaymentForm()
        stats = [
            {"label": "Residents", "value": User.objects.filter(role="resident").count(), "tone": "primary"},
            {"label": "Open Tickets", "value": Ticket.objects.exclude(status="closed").count(), "tone": "warning"},
            {"label": "Visitors Today", "value": Visitor.objects.filter(entry_time__date=timezone.now().date()).count(), "tone": "success"},
            {"label": "Pending Approvals", "value": User.objects.filter(role="resident", is_approved=False).count(), "tone": "info"},
        ]
        quick_links = [
            {"title": "Members", "subtitle": "Review registered users and resident approvals below.", "href": "#members-section", "tone": "primary"},
            {"title": "Tickets", "subtitle": "Track every maintenance issue in the complex.", "href": "/tickets/all/", "tone": "primary"},
            {"title": "Notices", "subtitle": "Create and manage notices for different audiences.", "href": "/notices/list/", "tone": "info"},
            {"title": "Assign Payment", "subtitle": "Create a new due for a resident.", "href": "#assign-payment", "tone": "warning"},
            {"title": "Payments", "subtitle": "Monitor dues collection and payment updates.", "href": "/payments/manage/", "tone": "warning"},
        ]
        pending_residents = User.objects.filter(
            role="resident",
            is_approved=False,
        ).order_by("date_joined")
        users_by_role = [
            {
                "label": "Residents",
                "key": "resident",
                "users": User.objects.filter(role="resident").order_by("username"),
            },
            {
                "label": "Staff",
                "key": "staff",
                "users": User.objects.filter(role="staff").order_by("username"),
            },
            {
                "label": "Security",
                "key": "security",
                "users": User.objects.filter(role="security").order_by("username"),
            },
            {
                "label": "Admins",
                "key": "admin",
                "users": User.objects.filter(role="admin").order_by("username"),
            },
        ]
        today = timezone.now().date()
        last_seven_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
        visitor_counts = {
            item["entry_time__date"]: item["total"]
            for item in Visitor.objects.filter(entry_time__date__gte=last_seven_days[0])
            .values("entry_time__date")
            .annotate(total=Count("id"))
        }
        ticket_category = list(
            Ticket.objects.values("category").annotate(total=Count("id")).order_by("category")
        )
        monthly_payments = list(
            Payment.objects.annotate(month_bucket=TruncMonth("created_at"))
            .values("month_bucket")
            .annotate(total=Sum("amount"))
            .order_by("month_bucket")
        )
        monthly_notices = list(
            Notice.objects.annotate(month_bucket=TruncMonth("created_at"))
            .values("month_bucket")
            .annotate(total=Count("id"))
            .order_by("month_bucket")
        )
        analytics = {
            "ticket_category_labels": [item["category"].title() for item in ticket_category],
            "ticket_category_values": [float(item["total"]) for item in ticket_category],
            "visitor_labels": [day.strftime("%d %b") for day in last_seven_days],
            "visitor_values": [visitor_counts.get(day, 0) for day in last_seven_days],
            "payment_labels": [
                item["month_bucket"].strftime("%b %Y") for item in monthly_payments if item["month_bucket"]
            ],
            "payment_values": [float(item["total"]) for item in monthly_payments if item["month_bucket"]],
            "notice_labels": [
                item["month_bucket"].strftime("%b %Y") for item in monthly_notices if item["month_bucket"]
            ],
            "notice_values": [item["total"] for item in monthly_notices if item["month_bucket"]],
        }

    return render(
        request,
        template,
        {
            "stats": stats,
            "quick_links": quick_links,
            "analytics": analytics,
            "pending_residents": pending_residents,
            "users_by_role": users_by_role,
            "assign_payment_form": assign_payment_form,
        },
    )


@login_required
def approve_resident(request, user_id):
    if request.user.role != "admin":
        messages.error(request, "Only admin can approve residents.")
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("dashboard")

    resident = get_object_or_404(User, id=user_id, role="resident")
    resident.is_approved = True
    resident.save(update_fields=["is_approved"])

    send_user_notification(
        resident,
        "AMS Apartment account approved",
        (
            f"Hello {resident.username},\n\n"
            "Your resident account has been approved by the admin team.\n"
            "You can now log in and access the AMS Apartment dashboard."
        ),
    )
    messages.success(request, f"{resident.username} has been approved successfully.")
    return redirect("dashboard")


class RegisterAPI(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        send_registration_notification(self.request, user)


class LoginAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        send_login_notification(request, user)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK,
        )


class LogoutAPI(APIView):
    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out successfully."})


class CurrentUserAPI(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
