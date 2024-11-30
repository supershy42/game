from django.urls import path
from .consumers import GameRoomConsumer

websocket_urlpatterns = [
    path("ws/gameRoom/<int:room_id>/", GameRoomConsumer.as_asgi()),
]
