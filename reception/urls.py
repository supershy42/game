from django.urls import path
from .views import CreateReceptionView, ReceptionListView, ReceptionJoinView, ReceptionInvitationView

urlpatterns = [
    path('create/', CreateReceptionView.as_view(), name='create-reception'),
    path('list/', ReceptionListView.as_view(), name='receptions'),
    path('<int:reception_id>/join/', ReceptionJoinView.as_view(), name='join-reception'),
    path('invite/', ReceptionInvitationView.as_view(), name='invite-reception')
]