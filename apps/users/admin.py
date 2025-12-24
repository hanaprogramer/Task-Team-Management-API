from django.contrib import admin
from . models import *

class AdminUser(admin.ModelAdmin):
    pass

admin.site.register(User, AdminUser)

# Register your models here.
