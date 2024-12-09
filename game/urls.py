from django.urls import path
from .views import CreateGameRoomView

urlpatterns = [
    path('create-room/', CreateGameRoomView.as_view(), name='create-room'),
]