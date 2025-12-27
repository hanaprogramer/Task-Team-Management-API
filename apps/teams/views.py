from .models import *
from .serializers import *
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied



class TeamsView(ModelViewSet):
    serializer_class = TeamSerialiser
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Teams.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().select_related('owner').prefetch_related('members')

    def perform_create(self, serializer):
        """
        هنگام ایجاد تیم، کاربر خودش را به عنوان مالک قرار می‌دهد
        """
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """
        فقط مالک تیم می‌تواند آن را ویرایش کند
        """
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied("You can only update your own teams")
        serializer.save()

    def perform_destroy(self, instance):
        """
        فقط مالک تیم می‌تواند آن را حذف کند
        """
        if instance.owner != self.request.user:
            raise PermissionDenied("You can only delete your own teams")
        instance.delete()