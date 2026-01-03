from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('', TasksViewSet, basename='task')
router.register(r'(?P<task_id>\d+)/comments', CommentViewSet, basename='task-comments')
# /api/tasks/<task_id>/comments/

urlpatterns = []
urlpatterns += router.urls
# GET /tasks/ 
# POST /tasks/ 
# GET /tasks/{id}/ 
# PUT/PATCH /tasks/{id}/ 
# DELETE /tasks/{id}/ 