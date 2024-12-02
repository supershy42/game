from django.urls import path, include

urlpatterns = [
    path('api/game/', include('game.urls')),
]
