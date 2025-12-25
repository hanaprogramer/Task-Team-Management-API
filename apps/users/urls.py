from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', UserViewSet, basename='user')

urlpatterns = [
    path('registration/', UserRegistrationView.as_view()),
]
urlpatterns += router.urls
