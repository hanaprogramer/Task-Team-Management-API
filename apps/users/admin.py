from django.contrib import admin
from . models import *

class AdminUser(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'last_login')
    list_filter = ('is_active', 'role')
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(User, AdminUser)

# Register your models here.
