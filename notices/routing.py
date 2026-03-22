from django.urls import path

from .consumers import NoticeNotificationConsumer


websocket_urlpatterns = [
    path("ws/notifications/", NoticeNotificationConsumer.as_asgi()),
]
