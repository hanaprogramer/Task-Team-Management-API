from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIRequestFactory

from apps.teams.models import Teams
from apps.projects.models import Project
from apps.tasks.models import Task, Comment
from apps.tasks.serializers import CommentSerializer

User = get_user_model()


class CommentSerializerTests(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

        # Users
        self.owner = User.objects.create_user(username="owner", password="1234StrongPass!")
        self.member = User.objects.create_user(username="member", password="1234StrongPass!")
        self.outsider = User.objects.create_user(username="outsider", password="1234StrongPass!")

        # Team
        self.team = Teams.objects.create(name="Team A", owner=self.owner)
        self.team.members.add(self.owner, self.member)

        # Project
        self.project = Project.objects.create(
            name="Project 1",
            team=self.team,
            created_by=self.owner,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_active=True
        )

        # Task
        self.task = Task.objects.create(
            title="Task 1",
            description="Task desc",
            project=self.project,
            assigned_to=self.member,
            created_by=self.owner,
            due_date=timezone.now().date() + timedelta(days=3)
        )

        # Comment
        self.comment = Comment.objects.create(
            task=self.task,
            author=self.member,
            content="Hello comment"
        )

    # ==================================================
    # READ OUTPUT
    # ==================================================
    def test_comment_serializer_read_output_contains_fields(self):
        serializer = CommentSerializer(self.comment)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("task", data)
        self.assertIn("task_detail", data)
        self.assertIn("author", data)
        self.assertIn("author_detail", data)
        self.assertIn("content", data)
        self.assertIn("created_at", data)

    # ==================================================
    # WRITE BEHAVIOR
    # ==================================================
    def test_comment_serializer_task_is_read_only(self):
        """
        task is read_only, so sending it in data should NOT be accepted.
        """
        request = self.factory.post("/")
        request.user = self.member

        payload = {
            "task": self.task.id,
            "content": "New comment"
        }

        serializer = CommentSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Because task is read_only, it should not appear in validated_data
        self.assertNotIn("task", serializer.validated_data)

    def test_comment_serializer_author_is_read_only(self):
        """
        author is read_only, so sending it in data should NOT be accepted.
        """
        request = self.factory.post("/")
        request.user = self.member

        payload = {
            "author": self.owner.id,
            "content": "New comment"
        }

        serializer = CommentSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)

        self.assertNotIn("author", serializer.validated_data)

    def test_comment_serializer_content_required(self):
        """
        content is required.
        """
        request = self.factory.post("/")
        request.user = self.member

        payload = {}
        serializer = CommentSerializer(data=payload, context={"request": request})

        self.assertFalse(serializer.is_valid())
        self.assertIn("content", serializer.errors)

    def test_comment_serializer_content_accepts_text(self):
        """
        Valid content should pass.
        """
        request = self.factory.post("/")
        request.user = self.member

        payload = {"content": "This is a comment"}
        serializer = CommentSerializer(data=payload, context={"request": request})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["content"], "This is a comment")
