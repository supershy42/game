from django.urls import path
from .consumers import ReceptionConsumer

websocket_urlpatterns = [
    path("ws/reception/<int:reception_id>/", ReceptionConsumer.as_asgi()),
]
