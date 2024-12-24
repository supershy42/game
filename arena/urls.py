from django.urls import path
from .views import MatchHistoryView

urlpatterns = [
    path('matches/', MatchHistoryView.as_view(), name='normal-matches')
]
