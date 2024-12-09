from django.urls import path
from .views import CreateReceptionView, ReceptionListView, ReceptionJoinView

urlpatterns = [
    path('/create/', CreateReceptionView.as_view(), name='create-reception'),
    path('s/', ReceptionListView.as_view(), name='receptions'),
    path('/<int:reception_id>/join/', ReceptionJoinView.as_view(), name='join-reception'),
]