from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIRequestFactory
from datetime import timedelta
from django.utils import timezone

from apps.teams.models import Teams
from apps.teams.serializers import TeamSerialiser


User = get_user_model()


class TeamSerializerTests(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

        # Users
        self.owner = User.objects.create_user(username="owner", password="1234")
        self.member1 = User.objects.create_user(username="member1", password="1234")
        self.member2 = User.objects.create_user(username="member2", password="1234")

        # Existing team
        self.team = Teams.objects.create(name="Team A", owner=self.owner)
        self.team.members.add(self.owner, self.member1)

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------
    def get_request(self, user):
        request = self.factory.post("/fake-url/")
        request.user = user
        return request

    def build_serializer(self, data=None, instance=None, user=None, partial=False):
        request = self.get_request(user or self.owner)
        return TeamSerialiser(
            instance=instance,
            data=data,
            partial=partial,
            context={"request": request}
        )

    # ========================================================
    # CREATE
    # ========================================================

    def test_create_team_success_without_members(self):
        """
        members optional:
        team should be created even if members is not provided.
        owner must be added automatically.
        """
        payload = {"name": "New Team"}
        serializer = self.build_serializer(data=payload, user=self.owner)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()

        self.assertEqual(team.owner, self.owner)
        self.assertTrue(team.members.filter(id=self.owner.id).exists())

    def test_create_team_success_with_members(self):
        """
        If members provided, they should be added along with owner.
        """
        payload = {
            "name": "New Team",
            "members": [self.member1.id, self.member2.id]
        }
        serializer = self.build_serializer(data=payload, user=self.owner)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()

        self.assertTrue(team.members.filter(id=self.owner.id).exists())
        self.assertTrue(team.members.filter(id=self.member1.id).exists())
        self.assertTrue(team.members.filter(id=self.member2.id).exists())

    def test_create_team_members_can_be_empty_list(self):
        """
        If members explicitly provided as empty list, it's still valid.
        Owner should still be member.
        """
        payload = {"name": "New Team", "members": []}
        serializer = self.build_serializer(data=payload, user=self.owner)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()

        self.assertTrue(team.members.filter(id=self.owner.id).exists())
        self.assertEqual(team.members.count(), 1)

    def test_create_team_owner_is_read_only(self):
        """
        If client tries to send owner, it must not override request.user.
        """
        payload = {
            "name": "New Team",
            "owner": self.member1.id,   # should be ignored
            "members": [self.member2.id]
        }
        serializer = self.build_serializer(data=payload, user=self.owner)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()

        self.assertEqual(team.owner, self.owner)
        self.assertTrue(team.members.filter(id=self.owner.id).exists())

    # ========================================================
    # UPDATE
    # ========================================================

    def test_update_team_name_success(self):
        """
        Updating name should work.
        """
        payload = {"name": "Updated Team Name"}
        serializer = self.build_serializer(instance=self.team, data=payload, user=self.owner, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()

        self.assertEqual(team.name, "Updated Team Name")

    def test_update_members_owner_cannot_be_removed(self):
        """
        When updating members, owner must remain in members.
        """
        payload = {"members": [self.member2.id]}  # owner not included
        serializer = self.build_serializer(instance=self.team, data=payload, user=self.owner, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()

        self.assertTrue(team.members.filter(id=self.owner.id).exists())
        self.assertTrue(team.members.filter(id=self.member2.id).exists())

    def test_update_members_none_means_do_not_change_members(self):
        """
        If members not provided in update, members should not be changed.
        """
        before_ids = list(self.team.members.values_list("id", flat=True))

        payload = {"name": "Only Name Changed"}
        serializer = self.build_serializer(instance=self.team, data=payload, user=self.owner, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()

        after_ids = list(team.members.values_list("id", flat=True))
        self.assertEqual(set(before_ids), set(after_ids))

    def test_owner_field_not_updatable(self):
        """
        Even if owner is sent on update, it should not change.
        """
        payload = {"owner": self.member2.id}
        serializer = self.build_serializer(instance=self.team, data=payload, user=self.owner, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        team = serializer.save()

        self.assertEqual(team.owner, self.owner)

    # ========================================================
    # READ OUTPUT
    # ========================================================

    def test_read_output_contains_details(self):
        """
    Serializer output should include owner_detail and members_detail.
    """
        request = self.get_request(self.owner)
        serializer = TeamSerialiser(instance=self.team, context={"request": request})
        data = serializer.data

        self.assertIn("owner_detail", data)
        self.assertIn("members_detail", data)
        self.assertIn("created_at", data)
        self.assertEqual(data["name"], self.team.name)
