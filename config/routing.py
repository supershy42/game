from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from reception.routing import websocket_urlpatterns
from config.middleware import CustomWsMiddleware

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": CustomWsMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
