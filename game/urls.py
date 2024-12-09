from django.urls import path
from .views import CreateReceptionView, ReceptionListView

urlpatterns = [
    path('create-reception/', CreateReceptionView.as_view(), name='create-reception'),
    path('receptions/', ReceptionListView.as_view(), name='receptions'),
]