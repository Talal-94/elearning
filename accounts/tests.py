from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import Block
from courses.models import Course, Enrollment

User = get_user_model()

class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username="teacher1", email="t@example.com", password="pass", role=User.TEACHER
        )
        self.student = User.objects.create_user(
            username="student1", email="s@example.com", password="pass", role=User.STUDENT
        )

    def login_teacher(self):
        self.client.login(username="teacher1", password="pass")

    def login_student(self):
        self.client.login(username="student1", password="pass")

    def test_login_logout_roundtrip(self):
        r = self.client.post(reverse("login"), {"username": "teacher1", "password": "pass"})
        self.assertEqual(r.status_code, 302)
        r = self.client.get(reverse("logout"))
        self.assertEqual(r.status_code, 302)

    def test_user_search_teacher_only(self):
        # teacher can access
        self.login_teacher()
        r = self.client.get(reverse("user_search"))
        self.assertEqual(r.status_code, 200)

        # student cannot
        self.client.logout()
        self.login_student()
        r = self.client.get(reverse("user_search"))
        self.assertEqual(r.status_code, 403)

    def test_profile_is_visible_to_others(self):
        self.login_student()
        r = self.client.get(reverse("user_profile", args=[self.teacher.username]))
        self.assertEqual(r.status_code, 200)

    def test_block_prevents_enrollment(self):
        # teacher has a course
        course = Course.objects.create(title="Physics", description="Basics", instructor=self.teacher)

        # teacher blocks student
        Block.objects.create(teacher=self.teacher, blocked=self.student)

        # student tries to enroll
        self.login_student()
        r = self.client.get(reverse("enroll", args=[course.id]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Enrollment.objects.filter(course=course, student=self.student).exists())
        # (Optional) check message appeared
        self.assertContains(r, "blocked", status_code=200)
