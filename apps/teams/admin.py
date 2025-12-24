from django.contrib import admin
from . models import *

class AdminTeams(admin.ModelAdmin):
    pass

admin.site.register(Teams, AdminTeams)