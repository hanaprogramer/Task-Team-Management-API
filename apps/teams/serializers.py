from .models import *
from rest_framework import serializers
from apps.users.serializers import *
from django.utils import timezone

class TeamSerialiser(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_detail = UserSerializer(source='owner', read_only=True)

    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    members_detail = UserSerializer(source='members', many=True, read_only=True)

    class Meta:
        model = Teams
        fields = ['id', 'name', 'owner_detail',
                  'members', 'members_detail', 'created_at']
        read_only_fields = ['id', 'created_at', 'owner_detail', 'members_detail']

    def create(self, validated_data):
        """
        ایجاد تیم:
        - owner از context/request می‌آید
        - owner همیشه به members اضافه می‌شود
        - اگر members ارسال شده باشد، owner هم در کنار آنها قرار می‌گیرد
        """
        request = self.context.get('request')
        owner = request.user

        members = validated_data.pop('members', [])
        team = Teams.objects.create(owner=owner, **validated_data)

        # owner همیشه عضو تیم است
        team.members.add(owner)

        # اگر members ارسال شده بود، اضافه شود
        for user in members:
            team.members.add(user)

        return team

    def update(self, instance, validated_data):
        """
        آپدیت تیم:
        - owner قابل تغییر نیست
        - members اگر ارسال شود، owner حذف نمی‌شود
        """
        members = validated_data.pop('members', None)

        # آپدیت فیلدهای ساده
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        # آپدیت اعضا (اختیاری)
        if members is not None:
            instance.members.set(members)
            instance.members.add(instance.owner)  # owner همیشه باید عضو باشد

        return instance    

