from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import Block
from courses.models import Course, Enrollment

User = get_user_model()

class AccountsViewExtraTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username="teach", email="t@example.com", password="x", role=User.TEACHER
        )
        self.student = User.objects.create_user(
            username="stud", email="s@example.com", password="x", role=User.STUDENT
        )

    def test_signup_get_renders(self):
        r = self.client.get(reverse("signup"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Create account")

    def test_signup_post_invalid_shows_errors(self):
        # Missing fields → form invalid, stays on page
        r = self.client.post(reverse("signup"), {"username": ""})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "This field is required", status_code=200)

    def test_signup_post_valid_creates_and_redirects(self):
        r = self.client.post(
            reverse("signup"),
            {"username": "newu", "email": "n@example.com", "password1": "Secret!234", "password2": "Secret!234", "role": User.STUDENT},
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(User.objects.filter(username="newu").exists())

    def test_logout_redirects(self):
        self.client.login(username="stud", password="x")
        r = self.client.get(reverse("logout"))
        self.assertEqual(r.status_code, 302)

    def test_user_search_returns_results_and_block_flag(self):
        # teacher searches, sees student result and can block
        self.client.login(username="teach", password="x")
        r = self.client.get(reverse("user_search"), {"q": "stud"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "stud")

        # Block the student → flag should flip
        r = self.client.get(reverse("user_block", args=[self.student.pk]), follow=True)
        self.assertEqual(r.status_code, 200)
        # search again to render 'Unblock' now
        r = self.client.get(reverse("user_search"), {"q": "stud"})
        self.assertContains(r, "Unblock")

    def test_block_and_unblock_endpoints(self):
        self.client.login(username="teach", password="x")
        # block
        r = self.client.get(reverse("user_block", args=[self.student.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Block.objects.filter(teacher=self.teacher, blocked=self.student).exists())
        # unblock
        r = self.client.get(reverse("user_unblock", args=[self.student.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Block.objects.filter(teacher=self.teacher, blocked=self.student).exists())

    def test_profile_view_student_branch_lists_enrolled_courses(self):
        # enroll student in a course so the student-branch has items
        course = Course.objects.create(title="Algebra", description="...", instructor=self.teacher)
        Enrollment.objects.create(course=course, student=self.student)

        # logged in as teacher, view the student's profile (covers the student branch)
        self.client.login(username="teach", password="x")
        r = self.client.get(reverse("user_profile", args=[self.student.username]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Enrolled Courses")
        self.assertContains(r, "Algebra")
