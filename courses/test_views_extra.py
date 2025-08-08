from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import Block
from courses.models import Course, Enrollment, StatusUpdate

User = get_user_model()

class CourseViewExtraTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user("t1", "t@example.com", "x", role=User.TEACHER)
        self.student = User.objects.create_user("s1", "s@example.com", "x", role=User.STUDENT)
        self.other = User.objects.create_user("u3", "u3@example.com", "x", role=User.STUDENT)
        self.course = Course.objects.create(title="Chem", description="desc", instructor=self.teacher)

    def login_teacher(self):
        self.client.login(username="t1", password="x")

    def login_student(self):
        self.client.login(username="s1", password="x")

    def test_course_list_renders(self):
        self.login_student()
        r = self.client.get(reverse("course_list"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Chem")

    def test_course_detail_renders(self):
        self.login_student()
        r = self.client.get(reverse("course_detail", args=[self.course.id]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Chem")

    def test_course_create_get_for_teacher(self):
        self.login_teacher()
        r = self.client.get(reverse("course_create"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Create")

    def test_material_upload_get_for_teacher(self):
        self.login_teacher()
        url = reverse("material_upload", args=[self.course.id])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_feedback_get_form_for_enrolled_student(self):
        Enrollment.objects.create(course=self.course, student=self.student)
        self.login_student()
        r = self.client.get(reverse("give_feedback", args=[self.course.id]))
        self.assertEqual(r.status_code, 200)

    def test_enroll_forbidden_for_teacher(self):
        self.login_teacher()
        r = self.client.get(reverse("enroll", args=[self.course.id]))
        self.assertEqual(r.status_code, 403)

    def test_post_status_invalid(self):
        # Empty content should fail form.is_valid() and keep count unchanged
        self.login_student()
        before = StatusUpdate.objects.filter(user=self.student).count()
        r = self.client.post(reverse("post_status"), {"content": ""}, follow=True)
        self.assertEqual(r.status_code, 200)
        after = StatusUpdate.objects.filter(user=self.student).count()
        self.assertEqual(before, after)

    def test_dashboard_teacher_lists_courses(self):
        self.login_teacher()
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Teacher Dashboard")
        self.assertContains(r, "Chem")

    def test_dashboard_student_filters_blocked_teacher(self):
        # Block this student from this teacher → course should not appear in "Available"
        Block.objects.create(teacher=self.teacher, blocked=self.student)
        self.login_student()
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Student Dashboard")
        # Available courses section should NOT include "Chem" for this student
        self.assertNotContains(r, "Enroll in this course")
        # sanity: an unenrolled other student (not blocked) should still see it
        self.client.logout()
        self.client.login(username="u3", password="x")
        r2 = self.client.get(reverse("home"))
        self.assertContains(r2, "Chem")
