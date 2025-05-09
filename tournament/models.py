from django.db import models
from arena.models import BaseMatch
import math

class Tournament(models.Model):
    class State(models.TextChoices):
        WAITING = 'waiting', 'Waiting'
        IN_PROGRESS = 'in_progress', 'In Progress'
        FINISHED = 'finished', 'Finished'
        
    VALID_PARTICIPANTS = [4,8,16]

    creator = models.IntegerField()
    name = models.CharField(max_length=40)
    max_participants = models.IntegerField(default=4)
    winner = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=20, choices=State.choices, default=State.WAITING)
    
    @property
    def current_participants(self):
        return self.tournamentparticipant_set.count()
    
    @property
    def total_rounds(self):
        return int(math.log2(self.max_participants))
    
    @classmethod
    def is_valid_participants(cls, value):
        return value in cls.VALID_PARTICIPANTS
    
    def is_full(self):
        return self.current_participants == self.max_participants
    
    
class TournamentParticipant(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('tournament', 'user_id')
        

class Round(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    round_number = models.PositiveIntegerField()
        
        
class TournamentMatch(BaseMatch):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    match_number = models.PositiveIntegerField()
    parent_match = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    parent_match_player_team = models.CharField(max_length=5, choices=BaseMatch.Team.choices, null=True, blank=True)