from django.contrib import admin
from .models import *

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'is_active', 'created_at')
    filter_by = ('is_active', 'team')

admin.site.register(Project, ProjectAdmin)
# Register your models here.
