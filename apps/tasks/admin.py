from django.contrib import admin
from .models import *


class TaskAdmin(admin.ModelAdmin):
    pass

admin.site.register(Task, TaskAdmin)

class CommentAdmin(admin.ModelAdmin):
    pass

admin.site.register(Comment, CommentAdmin)