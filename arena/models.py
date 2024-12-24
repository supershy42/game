from django.db import models

class BaseMatch(models.Model):
    class State(models.TextChoices):
        PENDING = 'pending', 'Pending'
        READY = 'ready', 'Ready to Start'
        FINISHED = 'finished', 'Finished'
        
    class Team(models.TextChoices):
        LEFT = 'left', 'Lending'
        RIGHT = 'right', 'Right'
    
    unique_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    left_player = models.IntegerField(null=True)
    right_player = models.IntegerField(null=True)
    left_player_score = models.IntegerField(default=0)
    right_player_score = models.IntegerField(default=0)
    winner = models.IntegerField(null=True)
    state = models.CharField(max_length=20, choices=State.choices, default=State.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
        
class NormalMatch(BaseMatch):
    pass