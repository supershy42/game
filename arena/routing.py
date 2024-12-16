from django.urls import path
from .consumers import ArenaConsumer

websocket_urlpatterns = [
    path("ws/arena/<int:arena_id>/", ArenaConsumer.as_asgi(), name="websocket_arena"),
]