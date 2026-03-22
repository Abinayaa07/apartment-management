# from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import VisitorForm
from .models import Visitor
from django.contrib import messages
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics, permissions

from .serializers import VisitorSerializer


@login_required
def add_visitor(request):

    if request.user.role not in ["security", "admin"]:
        messages.error(request, "Only security staff can access visitor entry.")
        return redirect("dashboard")

    if request.method == "POST":

        form = VisitorForm(request.POST)

        if form.is_valid():

            visitor = form.save(commit=False)

            visitor.security = request.user

            visitor.save()

            return redirect("visitor_list")

    else:
        form = VisitorForm()

    return render(request, "visitors/add_visitor.html", {"form": form})

@login_required
def visitor_list(request):

    if request.user.role not in ["security", "admin"]:
        
        return redirect("dashboard")

    visitors = Visitor.objects.all().order_by("-entry_time")
    query = request.GET.get("q", "").strip()
    flat_number = request.GET.get("flat_number", "").strip()
    visit_date = request.GET.get("date", "").strip()
    inside = request.GET.get("inside", "").strip()

    if query:
        visitors = visitors.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(purpose__icontains=query) |
            Q(flat_number__icontains=query) |
            Q(vehicle_number__icontains=query)
        )
    if flat_number:
        visitors = visitors.filter(flat_number__icontains=flat_number)
    if visit_date:
        visitors = visitors.filter(entry_time__date=visit_date)
    if inside == "yes":
        visitors = visitors.filter(exit_time__isnull=True)
    elif inside == "no":
        visitors = visitors.filter(exit_time__isnull=False)

    return render(
        request,
        "visitors/visitor_list.html",
        {
            "visitors": visitors,
            "filters": {
                "q": query,
                "flat_number": flat_number,
                "date": visit_date,
                "inside": inside,
            },
        }
    )

from django.shortcuts import get_object_or_404
from django.utils import timezone


@login_required
def visitor_exit(request, visitor_id):

    if request.user.role not in ["security", "admin"]:
        messages.error(request, "Only security staff can update visitor exit.")
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("visitor_list")

    visitor = get_object_or_404(Visitor, id=visitor_id)

    visitor.exit_time = timezone.now()

    visitor.save()

    return redirect("visitor_list")


class VisitorListAPI(generics.ListAPIView):
    serializer_class = VisitorSerializer

    def get_queryset(self):
        if self.request.user.role in ["security", "admin"]:
            return Visitor.objects.all().order_by("-entry_time")
        return Visitor.objects.none()


class VisitorCreateAPI(generics.CreateAPIView):
    serializer_class = VisitorSerializer

    def get_queryset(self):
        return Visitor.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role not in ["security", "admin"]:
            raise PermissionDenied("Only security or admin can add visitors.")
        serializer.save(security=self.request.user)

