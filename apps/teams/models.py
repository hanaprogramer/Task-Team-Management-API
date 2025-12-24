from django.db import models
from apps.users.models import User


class Teams(models.Model):
    name = models.CharField(max_length=30)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_teams')
    members = models.ManyToManyField(User, related_name='teams')
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name