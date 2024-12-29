from django.urls import path
from .views import (
    TournamentCreateView,
    TournamentListView,
    TournamentJoinView,
    TournamentBracketView,
    TournamentDetailView,
)

urlpatterns = [
    path('create/', TournamentCreateView.as_view(), name='create-tournament'),
    path('list/', TournamentListView.as_view(), name='tournaments'),
    path('<int:tournament_id>/join/', TournamentJoinView.as_view(), name='join-tournament'),
    path('<int:tournament_id>/bracket/', TournamentBracketView.as_view(), name='tournament-bracket'),
    path('<int:tournament_id>/detail/', TournamentDetailView.as_view(), name='tournament-detail'),
]