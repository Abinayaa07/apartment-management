from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name="home"),
    path('faq-chat/', views.faq_chat, name="faq_chat"),
    path('family/', views.my_family_details, name="my_family_details"),
    path('family/manage/', views.manage_family_details, name="manage_family_details"),
    path('register/', views.register, name="register"),
    path('login/', views.user_login, name="login"),
    path('logout/', views.user_logout, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('approve-resident/<int:user_id>/', views.approve_resident, name="approve_resident"),
    path("api/register/", views.RegisterAPI.as_view(), name="api_register"),
    path("api/login/", views.LoginAPI.as_view(), name="api_login"),
    path("api/logout/", views.LogoutAPI.as_view(), name="api_logout"),
    path("api/me/", views.CurrentUserAPI.as_view(), name="api_me"),

]
