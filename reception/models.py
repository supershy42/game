from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Reception(models.Model):
    class State(models.TextChoices):
        WAITING = 'waiting', 'Waiting'
        IN_PROGRESS = 'in_progress', 'In Progress'

    creator = models.IntegerField()
    name = models.CharField(max_length=20)
    password = models.CharField(max_length=20, blank=False, null=True)
    max_players = models.PositiveIntegerField(default=2)
    state = models.CharField(max_length=20, choices=State.choices, default=State.WAITING)
    
    @property
    def has_password(self):
        return self.password is not None
    
    def save(self, *args, **kwargs):
        if self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
        
    def check_password(self, raw_password):
        if self.password is None:
            return True
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return f"Reception: {self.name}"