from django.urls import path
from .views import CreateReceptionView, ReceptionsView

urlpatterns = [
    path('create-reception/', CreateReceptionView.as_view(), name='create-reception'),
    path('receptions/', ReceptionsView.as_view(), name='receptions'),
]