from django.urls import path
from . import views


urlpatterns = [

    path("create/", views.create_notice, name="create_notice"),

    path("list/", views.notice_list, name="notice_list"),
    path("delete/<int:notice_id>/", views.delete_notice, name="delete_notice"),
    path("api/list/", views.NoticeListAPI.as_view(), name="notice_api_list"),
    path("api/create/", views.NoticeCreateAPI.as_view(), name="notice_api_create"),
    path("api/delete/<int:pk>/", views.NoticeDeleteAPI.as_view(), name="notice_api_delete"),

]
