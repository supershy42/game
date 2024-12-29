from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from reception.routing import websocket_urlpatterns as reception_patterns
from arena.routing import websocket_urlpatterns as arena_patterns
from config.middleware import CustomWsMiddleware

django_asgi_app = get_asgi_application()

websocket_urlpatterns = reception_patterns + arena_patterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": CustomWsMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
