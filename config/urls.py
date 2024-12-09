from django.urls import path, include

urlpatterns = [
    path('api/reception', include('reception.urls')),
]
