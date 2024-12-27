from django.urls import path, include

urlpatterns = [
    path('api/reception/', include('reception.urls')),
    path('api/tournament/', include('tournament.urls')),
    path('api/arena/', include('arena.urls')),
]
