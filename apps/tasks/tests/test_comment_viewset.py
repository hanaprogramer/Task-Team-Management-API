from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.teams.models import Teams
from apps.projects.models import Project
from apps.tasks.models import Task, Comment

User = get_user_model()


class CommentViewSetTests(APITestCase):

    def setUp(self):
        # Users
        self.owner = User.objects.create_user(username="owner", password="1234StrongPass!")
        self.member = User.objects.create_user(username="member", password="1234StrongPass!")
        self.outsider = User.objects.create_user(username="outsider", password="1234StrongPass!")
        self.assigned = User.objects.create_user(username="assigned", password="1234StrongPass!")

        # Team
        self.team = Teams.objects.create(name="Team A", owner=self.owner)
        self.team.members.add(self.owner, self.member, self.assigned)

        # Another team for outsider tests
        self.team2_owner = User.objects.create_user(username="team2owner", password="1234StrongPass!")
        self.team2 = Teams.objects.create(name="Team B", owner=self.team2_owner)
        self.team2.members.add(self.team2_owner)

        # Project
        self.project = Project.objects.create(
            name="Project 1",
            team=self.team,
            created_by=self.owner,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_active=True
        )

        self.project2 = Project.objects.create(
            name="Project 2",
            team=self.team2,
            created_by=self.team2_owner,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_active=True
        )

        # Tasks
        self.task = Task.objects.create(
            title="Task 1",
            description="Task desc",
            project=self.project,
            assigned_to=self.assigned,
            created_by=self.owner,
            due_date=timezone.now().date() + timedelta(days=3)
        )

        self.task2 = Task.objects.create(
            title="Task 2",
            description="Task2 desc",
            project=self.project2,
            assigned_to=self.team2_owner,
            created_by=self.team2_owner,
            due_date=timezone.now().date() + timedelta(days=3)
        )

        # Comments
        self.comment_by_member = Comment.objects.create(
            task=self.task,
            author=self.member,
            content="Member comment"
        )

        self.comment_by_assigned = Comment.objects.create(
            task=self.task,
            author=self.assigned,
            content="Assigned comment"
        )

        # URLs
        self.list_url = reverse("task-comments-list", kwargs={"task_id": self.task.id})
        self.detail_url = reverse("task-comments-detail", kwargs={"task_id": self.task.id, "pk": self.comment_by_member.id})

        self.list_url_task2 = reverse("task-comments-list", kwargs={"task_id": self.task2.id})

    # ==================================================
    # AUTH
    # ==================================================
    def test_list_requires_auth(self):
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_requires_auth(self):
        res = self.client.post(self.list_url, {"content": "x"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==================================================
    # LIST
    # ==================================================
    def test_list_comments_success_for_team_owner(self):
        self.client.force_authenticate(user=self.owner)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_list_comments_success_for_team_member(self):
        self.client.force_authenticate(user=self.member)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_list_comments_success_for_assigned_user(self):
        self.client.force_authenticate(user=self.assigned)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_list_comments_forbidden_for_outsider(self):
        self.client.force_authenticate(user=self.outsider)
        res = self.client.get(self.list_url)
        # چون queryset محدود شده، یا 200 با لیست خالی یا 403
        # ما انتظار داریم کامنت‌ها رو نبینه
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if res.status_code == status.HTTP_200_OK:
            self.assertEqual(len(res.data), 0)

    # ==================================================
    # CREATE
    # ==================================================
    def test_create_comment_success_for_team_member(self):
        self.client.force_authenticate(user=self.member)
        payload = {"content": "New comment by member"}
        res = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data["content"], "New comment by member")
        self.assertEqual(res.data["author"], self.member.id)
        self.assertEqual(res.data["task"], self.task.id)

    def test_create_comment_forbidden_for_outsider_on_foreign_task(self):
        self.client.force_authenticate(user=self.outsider)
        payload = {"content": "I should not comment here"}
        res = self.client.post(self.list_url_task2, payload, format="json")

        # اگر permission create درست نوشته شده باشد باید 403 شود
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    # ==================================================
    # UPDATE
    # ==================================================
    def test_update_comment_success_for_author(self):
        self.client.force_authenticate(user=self.member)
        payload = {"content": "Updated content"}
        res = self.client.patch(self.detail_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data["content"], "Updated content")

    def test_update_comment_forbidden_for_non_author(self):
        self.client.force_authenticate(user=self.owner)
        payload = {"content": "Owner tries update"}
        res = self.client.patch(self.detail_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ==================================================
    # DELETE
    # ==================================================
    def test_delete_comment_success_for_author(self):
        self.client.force_authenticate(user=self.member)
        res = self.client.delete(self.detail_url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_comment_forbidden_for_non_author(self):
        self.client.force_authenticate(user=self.owner)
        res = self.client.delete(self.detail_url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
