from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class GameRoom(models.Model):
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=255, null=True, blank=True)
    max_players = models.PositiveIntegerField(default=2)
    
    def set_password(self, raw_password):
        if raw_password is not None:
            self.password = make_password(raw_password)
        else:
            self.password = None
        
    def check_password(self, raw_password):
        if self.password is None:
            return True
        elif self.password == "":
            return raw_password == ""
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return f"GameRoom: {self.name}"