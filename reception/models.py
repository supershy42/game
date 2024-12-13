from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Reception(models.Model):
    name = models.CharField(max_length=20)
    password = models.CharField(max_length=20, blank=False, null=True)
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
        return f"Reception: {self.name}"