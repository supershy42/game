from django.db import models

class BaseMatch(models.Model):
    class State(models.TextChoices):
        PENDING = 'pending', 'Pending'
        READY = 'ready', 'Ready to Start'
        STARTED = 'started', 'Started'
        FINISHED = 'finished', 'Finished'
    
    left_player = models.IntegerField(null=True)
    right_player = models.IntegerField(null=True)
    left_score = models.IntegerField(default=0)
    right_score = models.IntegerField(default=0)
    winner = models.IntegerField(null=True)
    state = models.CharField(max_length=20, choices=State.choices, default=State.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
        
class NormalMatch(BaseMatch):
    pass