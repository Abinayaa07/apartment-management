# from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import NoticeForm
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from core.notifications import send_notice_created_notification
from .realtime import broadcast_notice_created


def _notice_queryset_for_user(user):
    notices = Notice.objects.all().order_by("-created_at")
    if user.role == "admin":
        return notices
    if user.role == "staff":
        return notices.filter(audience__in=["all", "staff"])
    if user.role == "security":
        return notices.filter(audience__in=["all", "security"])
    return notices.filter(audience="all")


def _notice_recipient_emails(notice):
    from accounts.models import User

    users = User.objects.exclude(email="").exclude(email__isnull=True)
    if notice.audience == "staff":
        users = users.filter(role__in=["staff", "admin"])
    elif notice.audience == "security":
        users = users.filter(role__in=["security", "admin"])
    return list(users.values_list("email", flat=True))


@login_required
def create_notice(request):

    if request.user.role not in ["staff", "admin"]:
        return redirect("dashboard")

    if request.method == "POST":

        form = NoticeForm(request.POST, request.FILES)

        if form.is_valid():

            notice = form.save(commit=False)

            notice.created_by = request.user

            notice.save()
            broadcast_notice_created(notice)
            send_notice_created_notification(notice, _notice_recipient_emails(notice))
            return redirect("notice_list")

    else:
        form = NoticeForm()

    return render(
        request,
        "notices/create_notice.html",
        {"form": form}
    )

from .models import Notice


@login_required
def notice_list(request):
    notices = _notice_queryset_for_user(request.user)
    query = request.GET.get("q", "").strip()

    if query:
        notices = notices.filter(
            Q(title__icontains=query) |
            Q(message__icontains=query)
        )

    return render(
        request,
        "notices/notice_list.html",
        {
            "notices": notices,
            "filters": {"q": query},
            "can_manage_notices": request.user.role in ["staff", "admin"],
        }
    )


@login_required
def delete_notice(request, notice_id):
    if request.user.role not in ["staff", "admin"]:
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("notice_list")

    notice = get_object_or_404(Notice, id=notice_id)
    notice.delete()
    return redirect("notice_list")


from .serializers import NoticeSerializer


class NoticeListAPI(generics.ListAPIView):
    serializer_class = NoticeSerializer

    def get_queryset(self):
        return _notice_queryset_for_user(self.request.user)


class NoticeCreateAPI(generics.CreateAPIView):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer

    def perform_create(self, serializer):
        if self.request.user.role not in ["staff", "admin"]:
            raise PermissionDenied("Only staff or admin can create notices.")
        notice = serializer.save(created_by=self.request.user)
        broadcast_notice_created(notice)
        send_notice_created_notification(notice, _notice_recipient_emails(notice))


class NoticeDeleteAPI(generics.DestroyAPIView):
    serializer_class = NoticeSerializer

    def get_queryset(self):
        if self.request.user.role not in ["staff", "admin"]:
            raise PermissionDenied("Only staff or admin can delete notices.")
        return Notice.objects.all()
