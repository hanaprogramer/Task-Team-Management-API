from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.teams.models import Teams
from apps.projects.models import Project
from apps.tasks.models import Task


User = get_user_model()


class TasksViewSetTests(APITestCase):

    def setUp(self):
        # Users
        self.owner = User.objects.create_user(username="owner", password="1234", role="team_owner")
        self.member = User.objects.create_user(username="member", password="1234", role="member")
        self.outsider = User.objects.create_user(username="outsider", password="1234", role="member")

        # Team
        self.team = Teams.objects.create(name="Team A", owner=self.owner)
        self.team.members.add(self.member)

        # Project
        self.project = Project.objects.create(
            name="Project 1",
            team=self.team,
            created_by=self.owner
        )

        # Another team + project to test queryset isolation
        self.other_owner = User.objects.create_user(username="other_owner", password="1234", role="team_owner")
        self.other_team = Teams.objects.create(name="Team B", owner=self.other_owner)
        self.other_project = Project.objects.create(
            name="Project 2",
            team=self.other_team,
            created_by=self.other_owner
        )

        # Tasks
        self.task1 = Task.objects.create(
            title="Task 1",
            description="desc1",
            project=self.project,
            assigned_to=self.member,
            created_by=self.owner,
            due_date=timezone.now().date() + timedelta(days=3)
        )

        self.task2_other_team = Task.objects.create(
            title="Task other",
            description="other desc",
            project=self.other_project,
            assigned_to=None,
            created_by=self.other_owner,
            due_date=timezone.now().date() + timedelta(days=3)
        )

        # URLs from router basename='task'
        self.list_url = reverse("task-list")
        self.detail_url = reverse("task-detail", kwargs={"pk": self.task1.id})

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def auth(self, user):
        """Force authenticate user."""
        self.client.force_authenticate(user=user)

    def payload(self, **overrides):
        data = {
            "title": "New Task",
            "description": "New Description",
            "project": self.project.id,
            "assigned_to": self.member.id,
            "status": "todo",
            "priority": 2,
            "due_date": str(timezone.now().date() + timedelta(days=5)),
        }
        data.update(overrides)
        return data

    # ==========================================================
    # LIST
    # ==========================================================

    def test_list_requires_authentication(self):
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_only_team_tasks_for_owner(self):
        self.auth(self.owner)
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # should contain task1 but not task2_other_team
        ids = [item["title"] for item in res.data]
        self.assertIn(self.task1.title, ids)
        self.assertNotIn(self.task2_other_team.title, ids)

    def test_list_returns_only_team_tasks_for_member(self):
        self.auth(self.member)
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item["title"] for item in res.data]
        self.assertIn(self.task1.title, ids)
        self.assertNotIn(self.task2_other_team.title, ids)

    def test_list_returns_empty_for_outsider(self):
        self.auth(self.outsider)
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    # ==========================================================
    # RETRIEVE
    # ==========================================================

    def test_retrieve_task_success_for_owner(self):
        self.auth(self.owner)
        res = self.client.get(self.detail_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], self.task1.title)
        self.assertIn("project_detail", res.data)
        self.assertIn("assigned_to_detail", res.data)

    def test_retrieve_task_forbidden_for_outsider(self):
        """
        Outsider should NOT be able to retrieve this task.
        Depending on how DRF handles queryset filtering, it may return 404.
        """
        self.auth(self.outsider)
        res = self.client.get(self.detail_url)
        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    # ==========================================================
    # CREATE
    # ==========================================================

    def test_create_task_success_by_owner(self):
        self.auth(self.owner)
        res = self.client.post(self.list_url, self.payload(), format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["title"], "New Task")

        # confirm created_by set
        task = Task.objects.get(title="New Task")
        self.assertEqual(task.created_by, self.owner)

    def test_create_task_success_by_member(self):
        self.auth(self.member)
        res = self.client.post(self.list_url, self.payload(), format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        task = Task.objects.get(title="New Task")
        self.assertEqual(task.created_by, self.member)

    def test_create_task_fail_for_outsider(self):
        self.auth(self.outsider)
        res = self.client.post(self.list_url, self.payload(), format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You do not have permission to create a task in this project.", str(res.data))

    def test_create_task_fail_due_date_in_past(self):
        self.auth(self.owner)
        res = self.client.post(
            self.list_url,
            self.payload(due_date=str(timezone.now().date() - timedelta(days=1))),
            format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Due date cannot be in the past.", str(res.data))

    def test_create_task_fail_assigned_to_not_in_team(self):
        self.auth(self.owner)
        res = self.client.post(
            self.list_url,
            self.payload(assigned_to=self.outsider.id),
            format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Assigned user must be a member of the team.", str(res.data))

    # ==========================================================
    # UPDATE
    # ==========================================================

    def test_update_structural_by_creator_success(self):
        self.auth(self.owner)  # owner is creator
        res = self.client.patch(self.detail_url, {"title": "Updated title"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_structural_by_member_fail(self):
        """
        member is assigned user, but NOT creator and NOT team owner,
        so structural changes should fail by serializer validate()
        """
        self.auth(self.member)
        res = self.client.patch(self.detail_url, {"title": "Updated title"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Only task creator or team owner can modify task details.", str(res.data))

    def test_update_execution_by_assigned_user_success(self):
        self.auth(self.member)
        res = self.client.patch(self.detail_url, {"status": "doing"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_execution_by_outsider_forbidden(self):
        """
        Outsider doesn't have permission even at view-level,
        should get 403 or 404 (because queryset does not include it)
        """
        self.auth(self.outsider)
        res = self.client.patch(self.detail_url, {"status": "done"}, format="json")
        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    def test_update_assigned_to_by_member_fail(self):
        self.auth(self.member)
        res = self.client.patch(self.detail_url, {"assigned_to": self.owner.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Only team owner can change task assignee.", str(res.data))

    def test_update_assigned_to_by_owner_success(self):
        self.auth(self.owner)
        res = self.client.patch(self.detail_url, {"assigned_to": self.owner.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_due_date_in_past_fail(self):
        self.auth(self.owner)
        res = self.client.patch(
            self.detail_url,
            {"due_date": str(timezone.now().date() - timedelta(days=5))},
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Due date cannot be in the past.", str(res.data))

    # ==========================================================
    # DELETE
    # ==========================================================

    def test_delete_task_by_member_success(self):
        self.auth(self.member)
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_task_forbidden_for_outsider(self):
        self.auth(self.outsider)
        res = self.client.delete(self.detail_url)
        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
