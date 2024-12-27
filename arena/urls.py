from django.urls import path
from .views import MatchHistoryView

urlpatterns = [
    path('matches/<int:user_id>/', MatchHistoryView.as_view(), name='normal-matches')
]
