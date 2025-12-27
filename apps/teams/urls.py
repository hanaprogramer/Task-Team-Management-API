from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', TeamsView, basename='team')

urlpatterns = []
urlpatterns += router.urls
