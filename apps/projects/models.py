from django.db import models
from apps.teams.models import *
from apps.users.models import *

class Project(models.Model):
    name = models.CharField(max_length=30)
    team = models.ForeignKey(Teams, on_delete=models.CASCADE, related_name='projects')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    start_date = models.DateField(null=True, blank=True)    
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Create your models here.
