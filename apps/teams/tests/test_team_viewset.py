from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.teams.models import Teams

User = get_user_model()


class TeamsViewSetTests(APITestCase):

    def setUp(self):
        # Users
        self.owner = User.objects.create_user(username="owner", password="1234")
        self.member = User.objects.create_user(username="member", password="1234")
        self.outsider = User.objects.create_user(username="outsider", password="1234")

        # Teams
        self.team1 = Teams.objects.create(name="Team 1", owner=self.owner)
        self.team1.members.add(self.owner, self.member)

        self.team2 = Teams.objects.create(name="Team 2", owner=self.member)
        self.team2.members.add(self.member)

        # URLs (router basename='team')
        self.list_url = reverse("teams-list")
        self.detail_url = reverse("teams-detail", kwargs={"pk": self.team1.id})

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def auth(self, user):
        self.client.force_authenticate(user=user)

    # =========================================================
    # LIST
    # =========================================================

    def test_list_requires_authentication(self):
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_only_related_teams_for_owner(self):
        self.auth(self.owner)
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = [t["name"] for t in res.data]
        self.assertIn("Team 1", names)
        self.assertNotIn("Team 2", names)

    def test_list_returns_only_related_teams_for_member(self):
        self.auth(self.member)
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = [t["name"] for t in res.data]
        # member is part of team1 and owner of team2
        self.assertIn("Team 1", names)
        self.assertIn("Team 2", names)

    def test_list_returns_empty_for_outsider(self):
        self.auth(self.outsider)
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    # =========================================================
    # RETRIEVE
    # =========================================================

    def test_retrieve_team_success_for_owner(self):
        self.auth(self.owner)
        res = self.client.get(self.detail_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], self.team1.name)
        self.assertIn("owner_detail", res.data)
        self.assertIn("members_detail", res.data)

    def test_retrieve_team_not_found_for_outsider(self):
        """
        Outsider cannot see the object at all due to queryset restriction.
        DRF usually returns 404 instead of 403.
        """
        self.auth(self.outsider)
        res = self.client.get(self.detail_url)

        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    # =========================================================
    # CREATE
    # =========================================================

    def test_create_team_success_without_members(self):
        """
        members is optional.
        owner must be set automatically and added to members.
        """
        self.auth(self.owner)
        payload = {"name": "New Team"}
        res = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)


        team = Teams.objects.get(name="New Team")
        self.assertEqual(team.owner, self.owner)
        self.assertTrue(team.members.filter(id=self.owner.id).exists())

    def test_create_team_success_with_members(self):
        self.auth(self.owner)
        payload = {"name": "Team X", "members": [self.member.id]}
        res = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        team = Teams.objects.get(name="Team X")
        self.assertTrue(team.members.filter(id=self.owner.id).exists())
        self.assertTrue(team.members.filter(id=self.member.id).exists())

    def test_create_team_owner_cannot_be_overridden(self):
        """
        If client tries to send owner, it should not override request.user.
        """
        self.auth(self.owner)
        payload = {"name": "Team Y", "owner": self.member.id}
        res = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        team = Teams.objects.get(name="Team Y")
        self.assertEqual(team.owner, self.owner)

    # =========================================================
    # UPDATE
    # =========================================================

    def test_update_team_success_for_owner(self):
        self.auth(self.owner)
        payload = {"name": "Updated Team 1"}
        res = self.client.patch(self.detail_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.team1.refresh_from_db()
        self.assertEqual(self.team1.name, "Updated Team 1")

    def test_update_team_forbidden_for_member(self):
        """
        member is in team, but is not owner => cannot update.
        """
        self.auth(self.member)
        payload = {"name": "Hacked Name"}
        res = self.client.patch(self.detail_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_team_forbidden_for_outsider(self):
        self.auth(self.outsider)
        payload = {"name": "Hacked Name"}
        res = self.client.patch(self.detail_url, payload, format="json")

        # likely 404 because queryset hides it
        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    def test_update_members_owner_cannot_be_removed(self):
        """
        Owner must remain member even if members set does not include them.
        """
        self.auth(self.owner)
        payload = {"members": [self.member.id]}  # owner missing
        res = self.client.patch(self.detail_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.team1.refresh_from_db()
        self.assertTrue(self.team1.members.filter(id=self.owner.id).exists())

    # =========================================================
    # DELETE
    # =========================================================

    def test_delete_team_success_for_owner(self):
        self.auth(self.owner)
        res = self.client.delete(self.detail_url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Teams.objects.filter(id=self.team1.id).exists())

    def test_delete_team_forbidden_for_member(self):
        self.auth(self.member)
        res = self.client.delete(self.detail_url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_team_forbidden_for_outsider(self):
        self.auth(self.outsider)
        res = self.client.delete(self.detail_url)

        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
