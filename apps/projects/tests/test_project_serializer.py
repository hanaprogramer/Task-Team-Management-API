from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIRequestFactory

from apps.teams.models import Teams
from apps.projects.models import Project
from apps.projects.serializers import ProjectsSerializer

User = get_user_model()


class ProjectSerializerTests(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

        # Users
        self.team_owner = User.objects.create_user(username="team_owner", password="1234")
        self.member = User.objects.create_user(username="member", password="1234")
        self.outsider = User.objects.create_user(username="outsider", password="1234")

        self.project_creator = User.objects.create_user(username="creator", password="1234")

        # Teams
        self.team1 = Teams.objects.create(name="Team 1", owner=self.team_owner)
        self.team1.members.add(self.team_owner, self.member)

        self.team2 = Teams.objects.create(name="Team 2", owner=self.team_owner)
        self.team2.members.add(self.team_owner)

        # Existing project
        self.project = Project.objects.create(
            name="Project A",
            team=self.team1,
            created_by=self.project_creator,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            is_active=True,
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def get_request(self, user):
        request = self.factory.post("/fake-url/")
        request.user = user
        return request

    def build_serializer(self, *, user, data=None, instance=None, partial=False):
        request = self.get_request(user)
        return ProjectsSerializer(
            instance=instance,
            data=data,
            partial=partial,
            context={"request": request}
        )

    # =========================================================
    # CREATE
    # =========================================================

    def test_create_project_success_by_team_owner(self):
        payload = {"name": "New Project", "team": self.team1.id}
        serializer = self.build_serializer(user=self.team_owner, data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_project_success_by_team_member(self):
        payload = {"name": "New Project 2", "team": self.team1.id}
        serializer = self.build_serializer(user=self.member, data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_project_fail_for_outsider(self):
        payload = {"name": "Outsider Project", "team": self.team1.id}
        serializer = self.build_serializer(user=self.outsider, data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("team", serializer.errors)

    def test_create_project_fail_duplicate_name_in_same_team(self):
        payload = {"name": "Project A", "team": self.team1.id}  # same as existing in same team
        serializer = self.build_serializer(user=self.team_owner, data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_create_project_success_duplicate_name_in_different_team(self):
        payload = {"name": "Project A", "team": self.team2.id}  # same name but different team => ok
        serializer = self.build_serializer(user=self.team_owner, data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_project_fail_end_date_before_start_date(self):
        payload = {
            "name": "Bad Dates Project",
            "team": self.team1.id,
            "start_date": timezone.now().date(),
            "end_date": timezone.now().date() - timedelta(days=2),
        }
        serializer = self.build_serializer(user=self.team_owner, data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    # =========================================================
    # UPDATE - NAME VALIDATION
    # =========================================================

    def test_update_project_same_name_should_not_fail(self):
        payload = {"name": "Project A"}  # same name as itself
        serializer = self.build_serializer(user=self.team_owner, instance=self.project, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_project_rename_to_existing_name_should_fail(self):
        # Create another project in same team
        Project.objects.create(name="Project B", team=self.team1, created_by=self.team_owner)

        payload = {"name": "Project B"}  # rename to existing name
        serializer = self.build_serializer(user=self.team_owner, instance=self.project, data=payload, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    # =========================================================
    # UPDATE - TEAM CHANGE PERMISSION
    # =========================================================

    def test_update_project_change_team_only_owner_or_creator_allowed(self):
        payload = {"team": self.team2.id}

        # member is not team owner and not project creator => should fail
        serializer = self.build_serializer(user=self.member, instance=self.project, data=payload, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("team", serializer.errors)

        # project creator => should pass
        serializer = self.build_serializer(user=self.project_creator, instance=self.project, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # team owner => should pass
        serializer = self.build_serializer(user=self.team_owner, instance=self.project, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    # =========================================================
    # UPDATE - is_active PERMISSION
    # =========================================================

    def test_update_is_active_only_owner_or_creator_allowed(self):
        payload = {"is_active": False}

        # member => fail
        serializer = self.build_serializer(user=self.member, instance=self.project, data=payload, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("is_active", serializer.errors)

        # creator => pass
        serializer = self.build_serializer(user=self.project_creator, instance=self.project, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # owner => pass
        serializer = self.build_serializer(user=self.team_owner, instance=self.project, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    # =========================================================
    # READ OUTPUT
    # =========================================================

    def test_read_output_contains_team_detail_and_created_by_detail(self):
        request = self.get_request(self.team_owner)
        serializer = ProjectsSerializer(instance=self.project, context={"request": request})
        data = serializer.data

        self.assertIn("team_detail", data)
        self.assertIn("created_by_detail", data)
        self.assertEqual(data["name"], self.project.name)
