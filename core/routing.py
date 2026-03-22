from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter

import notices.routing


websocket_urlpatterns = notices.routing.websocket_urlpatterns

application = AuthMiddlewareStack(
    URLRouter(websocket_urlpatterns)
)
