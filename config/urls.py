from django.urls import path, include

urlpatterns = [
    path('api/game/reception/', include('reception.urls')),
    path('api/game/tournament/', include('tournament.urls')),
    path('api/game/arena/', include('arena.urls')),
]
