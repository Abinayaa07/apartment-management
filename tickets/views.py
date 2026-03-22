# from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import TicketForm
from .models import Ticket
from django.contrib import messages
from rest_framework import generics, permissions

from core.notifications import send_ticket_created_notification
from .serializers import TicketSerializer


@login_required
def create_ticket(request):

    if request.method == "POST":

        form = TicketForm(request.POST, request.FILES)

        if form.is_valid():

            ticket = form.save(commit=False)

            ticket.resident = request.user

            ticket.save()
            send_ticket_created_notification(request, request.user, ticket)
            messages.success(request, "Ticket created successfully.")

            return redirect("my_tickets")

    else:
        form = TicketForm()

    return render(request, "tickets/create_ticket.html", {"form": form})


@login_required
def my_tickets(request):
    tickets = request.user.tickets.all().order_by("-created_at")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()

    if query:
        tickets = tickets.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )
    if status:
        tickets = tickets.filter(status=status)
    if category:
        tickets = tickets.filter(category=category)

    return render(
        request,
        "tickets/my_tickets.html",
        {
            "tickets": tickets,
            "status_choices": Ticket.STATUS_CHOICES,
            "category_choices": Ticket.CATEGORY_CHOICES,
            "filters": {"q": query, "status": status, "category": category},
        }
    )

@login_required
def all_tickets(request):

    if request.user.role not in ["staff", "admin"]:
        messages.error(request, "Only security staff can access visitor entry.")
        return redirect("dashboard")

    tickets = Ticket.objects.all().order_by("-created_at")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()
    resident = request.GET.get("resident", "").strip()

    if query:
        tickets = tickets.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query) |
            Q(resident__username__icontains=query)
        )
    if status:
        tickets = tickets.filter(status=status)
    if category:
        tickets = tickets.filter(category=category)
    if resident:
        tickets = tickets.filter(resident__username__icontains=resident)

    return render(
        request,
        "tickets/all_tickets.html",
        {
            "tickets": tickets,
            "status_choices": Ticket.STATUS_CHOICES,
            "category_choices": Ticket.CATEGORY_CHOICES,
            "filters": {
                "q": query,
                "status": status,
                "category": category,
                "resident": resident,
            },
        }
    )

from django.shortcuts import get_object_or_404


@login_required
def update_ticket_status(request, ticket_id):

    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.user.role not in ["staff", "admin"]:
        messages.error(request, "Only security staff can access visitor entry.")
        return redirect("dashboard")

    if request.method == "POST":

        status = request.POST.get("status")

        ticket.status = status

        ticket.save()

        return redirect("all_tickets")

    return render(
        request,
        "tickets/update_ticket.html",
        {"ticket": ticket}
    )


class TicketListAPI(generics.ListAPIView):
    serializer_class = TicketSerializer

    def get_queryset(self):
        if self.request.user.role in ["staff", "admin"]:
            return Ticket.objects.all().order_by("-created_at")
        return Ticket.objects.filter(resident=self.request.user).order_by("-created_at")


class TicketCreateAPI(generics.CreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.all()

    def perform_create(self, serializer):
        ticket = serializer.save(resident=self.request.user)
        send_ticket_created_notification(self.request, self.request.user, ticket)


class TicketUpdateAPI(generics.UpdateAPIView):
    serializer_class = TicketSerializer

    def get_queryset(self):
        if self.request.user.role in ["staff", "admin"]:
            return Ticket.objects.all()
        return Ticket.objects.filter(resident=self.request.user)


class TicketDeleteAPI(generics.DestroyAPIView):
    serializer_class = TicketSerializer

    def get_queryset(self):
        if self.request.user.role in ["staff", "admin"]:
            return Ticket.objects.all()
        return Ticket.objects.filter(resident=self.request.user)


