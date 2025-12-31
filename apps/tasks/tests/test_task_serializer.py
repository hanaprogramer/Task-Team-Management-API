from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.exceptions import ValidationError
from apps.tasks.models import *
from apps.projects.models import *
from apps.teams.models import *
from apps.tasks.serializers import *
from apps.projects.serializers import *
from apps.teams.serializers import *

User = get_user_model()

class TaskSerializerTests(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

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

        # Task
        self.task = Task.objects.create(
            title="Task 1",
            description="desc",
            project=self.project,
            assigned_to=self.member,
            created_by=self.owner,
            due_date=timezone.now().date() + timedelta(days=3),
        )

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------
    def get_request(self, user):
        request = self.factory.post("/fake-url/")
        request.user = user
        return request

    def get_valid_payload(self, **overrides):
        payload = {
            "title": "New Task",
            "description": "New Description",
            "project": self.project.id,
            "assigned_to": self.member.id,
            "status": "todo",
            "priority": 2,
            "due_date": timezone.now().date() + timedelta(days=5),
        }
        payload.update(overrides)
        return payload

    # ========================================================
    # CREATE TESTS
    # ========================================================

    def test_create_task_success_by_team_owner(self):
        """Team owner can create task."""
        request = self.get_request(self.owner)
        serializer = TaskSerializer(
            data=self.get_valid_payload(),
            context={"request": request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_task_success_by_team_member(self):
        """Team member can create task."""
        request = self.get_request(self.member)
        serializer = TaskSerializer(
            data=self.get_valid_payload(),
            context={"request": request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_task_fail_for_outsider(self):
        """Non team members cannot create tasks."""
        request = self.get_request(self.outsider)

        serializer = TaskSerializer(
            data=self.get_valid_payload(),
            context={"request": request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("You do not have permission to create a task in this project.", str(serializer.errors))

    def test_create_task_fail_assigned_to_not_in_team(self):
        """assigned_to must be member of the team."""
        request = self.get_request(self.owner)

        payload = self.get_valid_payload(assigned_to=self.outsider.id)

        serializer = TaskSerializer(data=payload, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Assigned user must be a member of the team.", str(serializer.errors))

    def test_create_task_success_assigned_to_null(self):
        """assigned_to is optional and can be null."""
        request = self.get_request(self.owner)
        payload = self.get_valid_payload(assigned_to=None)

        serializer = TaskSerializer(data=payload, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_task_fail_due_date_in_past(self):
        """due_date cannot be in the past."""
        request = self.get_request(self.owner)

        payload = self.get_valid_payload(
            due_date=timezone.now().date() - timedelta(days=1)
        )
        serializer = TaskSerializer(data=payload, context={"request": request})

        self.assertFalse(serializer.is_valid())
        self.assertIn("Due date cannot be in the past.", str(serializer.errors))

    # ========================================================
    # UPDATE TESTS
    # ========================================================

    def test_update_structural_fields_by_creator_success(self):
        """Creator can update structural fields (title, description, due_date)."""
        request = self.get_request(self.owner)

        serializer = TaskSerializer(
            instance=self.task,
            data={"title": "Updated title"},
            partial=True,
            context={"request": request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_structural_fields_by_non_creator_fail(self):
        """Non creator & non owner cannot update structural fields."""
        request = self.get_request(self.member)

        serializer = TaskSerializer(
            instance=self.task,
            data={"title": "Updated title"},
            partial=True,
            context={"request": request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("Only task creator or team owner can modify task details.", str(serializer.errors))

    def test_update_execution_fields_by_assigned_user_success(self):
        """Assigned user can update execution fields (status, priority)."""
        request = self.get_request(self.member)

        serializer = TaskSerializer(
            instance=self.task,
            data={"status": "doing"},
            partial=True,
            context={"request": request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_execution_fields_by_outsider_fail(self):
        """Only assigned user or owner can update status/priority."""
        request = self.get_request(self.outsider)

        serializer = TaskSerializer(
            instance=self.task,
            data={"status": "done"},
            partial=True,
            context={"request": request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("Only assigned user or team owner can update task status or priority.", str(serializer.errors))

    def test_update_assigned_to_only_owner_success(self):
        """Only team owner can change assignee."""
        request = self.get_request(self.owner)

        serializer = TaskSerializer(
            instance=self.task,
            data={"assigned_to": self.owner.id},  # assign to owner is ok
            partial=True,
            context={"request": request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_assigned_to_by_member_fail(self):
        """Non owner cannot change assigned_to."""
        request = self.get_request(self.member)

        serializer = TaskSerializer(
            instance=self.task,
            data={"assigned_to": self.owner.id},
            partial=True,
            context={"request": request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("Only team owner can change task assignee.", str(serializer.errors))

    def test_update_assigned_to_fail_if_new_assignee_not_in_team(self):
        """Even owner cannot assign to outsider."""
        request = self.get_request(self.owner)

        serializer = TaskSerializer(
            instance=self.task,
            data={"assigned_to": self.outsider.id},
            partial=True,
            context={"request": request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("Assigned user must be a member of the team.", str(serializer.errors))

    def test_update_due_date_in_past_fail(self):
        """Cannot update due_date to past."""
        request = self.get_request(self.owner)

        serializer = TaskSerializer(
            instance=self.task,
            data={"due_date": timezone.now().date() - timedelta(days=2)},
            partial=True,
            context={"request": request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("Due date cannot be in the past.", str(serializer.errors))

    # ========================================================
    # READ FIELDS TESTS (project_detail & assigned_to_detail)
    # ========================================================

    def test_serializer_read_fields_exist(self):
        """project_detail and assigned_to_detail should appear in output."""
        request = self.get_request(self.owner)

        serializer = TaskSerializer(instance=self.task, context={"request": request})
        data = serializer.data

        self.assertIn("project_detail", data)
        self.assertIn("assigned_to_detail", data)

        # write-only field should not appear in read output:
        # (project exists only as a write field but is in Meta fields too,
        # so it might still appear depending on DRF behavior; but it is write_only=True)
        self.assertNotIn("project", data)
