from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.teams.models import Teams
from apps.projects.models import Project

User = get_user_model()


class ProjectsViewSetTests(APITestCase):

    def setUp(self):
        # Users
        self.team_owner = User.objects.create_user(username="team_owner", password="1234")
        self.member = User.objects.create_user(username="member", password="1234")
        self.outsider = User.objects.create_user(username="outsider", password="1234")
        self.creator = User.objects.create_user(username="creator", password="1234")

        # Teams
        self.team1 = Teams.objects.create(name="Team 1", owner=self.team_owner)
        self.team1.members.add(self.team_owner, self.member)

        self.team2 = Teams.objects.create(name="Team 2", owner=self.team_owner)
        self.team2.members.add(self.team_owner)

        # Projects
        self.project1 = Project.objects.create(
            name="Project 1",
            team=self.team1,
            created_by=self.creator,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=5),
            is_active=True
        )
        self.project2 = Project.objects.create(
            name="Project 2",
            team=self.team2,
            created_by=self.team_owner,
            is_active=True
        )

        # URLs
        # ✅ اگر basename تو router = 'projects' باشد:
        self.list_url = reverse("projects-list")
        self.detail_url = reverse("projects-detail", kwargs={"pk": self.project1.id})

        # اگر basename تو router = 'project' بود این دو خطو جایگزین کن:
        # self.list_url = reverse("project-list")
        # self.detail_url = reverse("project-detail", kwargs={"pk": self.project1.id})

    def auth(self, user):
        self.client.force_authenticate(user=user)

    # =========================================================
    # LIST
    # =========================================================

    def test_list_requires_auth(self):
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_only_related_projects_for_owner(self):
        self.auth(self.team_owner)
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = [p["name"] for p in res.data]
        self.assertIn("Project 1", names)  # owner is owner of team1
        self.assertIn("Project 2", names)  # owner is owner of team2

    def test_list_returns_only_related_projects_for_member(self):
        self.auth(self.member)
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = [p["name"] for p in res.data]
        self.assertIn("Project 1", names)  # member of team1
        self.assertNotIn("Project 2", names)  # not member of team2

    def test_list_empty_for_outsider(self):
        self.auth(self.outsider)
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    # =========================================================
    # RETRIEVE
    # =========================================================

    def test_retrieve_project_success_for_owner(self):
        self.auth(self.team_owner)
        res = self.client.get(self.detail_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], self.project1.name)

    def test_retrieve_project_for_outsider_not_found(self):
        self.auth(self.outsider)
        res = self.client.get(self.detail_url)

        # چون get_queryset فیلتر می‌کنه، معمولاً 404 می‌گیری
        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    # =========================================================
    # CREATE
    # =========================================================

    def test_create_project_success_for_team_owner(self):
        self.auth(self.team_owner)
        payload = {
            "name": "New Project",
            "team": self.team1.id,
        }
        res = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Project.objects.filter(name="New Project").exists())

    def test_create_project_success_for_team_member(self):
        self.auth(self.member)
        payload = {
            "name": "Member Project",
            "team": self.team1.id,
        }
        res = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_project_fail_for_outsider(self):
        self.auth(self.outsider)
        payload = {
            "name": "Outsider Project",
            "team": self.team1.id,
        }
        res = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================
    # UPDATE
    # =========================================================

    def test_update_project_success_for_team_owner(self):
        self.auth(self.team_owner)
        payload = {"name": "Updated Project"}
        res = self.client.patch(self.detail_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.project1.refresh_from_db()
        self.assertEqual(self.project1.name, "Updated Project")

    def test_update_project_forbidden_for_member(self):
        self.auth(self.member)
        payload = {"name": "Hacked"}
        res = self.client.patch(self.detail_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_project_forbidden_for_outsider(self):
        self.auth(self.outsider)
        payload = {"name": "Hacked"}
        res = self.client.patch(self.detail_url, payload, format="json")

        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    # =========================================================
    # DELETE
    # =========================================================

    def test_delete_project_success_for_team_owner(self):
        self.auth(self.team_owner)
        res = self.client.delete(self.detail_url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=self.project1.id).exists())

    def test_delete_project_forbidden_for_member(self):
        self.auth(self.member)
        res = self.client.delete(self.detail_url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_project_forbidden_for_outsider(self):
        self.auth(self.outsider)
        res = self.client.delete(self.detail_url)

        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
