from django.urls import path
from .consumers import GameRoomConsumer

websocket_urlpatterns = [
    path("gameRoom/<int:room_id>/", GameRoomConsumer.as_asgi()),
]
