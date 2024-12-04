from django.urls import path
from .views import CreateReceptionView

urlpatterns = [
    path('create-reception/', CreateReceptionView.as_view(), name='create-reception'),
]