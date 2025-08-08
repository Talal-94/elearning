import os
import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from accounts.models import Block
from courses.models import Course, Enrollment, Feedback, Material, StatusUpdate

User = get_user_model()

# create a temp MEDIA_ROOT so test uploads don't pollute your project
_TEST_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=_TEST_MEDIA_ROOT)
class CoursesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            shutil.rmtree(_TEST_MEDIA_ROOT)
        except Exception:
            pass

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username="teacher1", email="t@example.com", password="pass", role=User.TEACHER
        )
        self.student = User.objects.create_user(
            username="student1", email="s@example.com", password="pass", role=User.STUDENT
        )
        self.course = Course.objects.create(
            title="Chemistry", description="Intro", instructor=self.teacher
        )

    def login_teacher(self):
        self.client.login(username="teacher1", password="pass")

    def login_student(self):
        self.client.login(username="student1", password="pass")

    # ----- Course creation -----
    def test_teacher_can_create_course(self):
        self.login_teacher()
        r = self.client.post(reverse("course_create"), {"title": "Math", "description": "Algebra"})
        self.assertEqual(r.status_code, 302)
        c = Course.objects.get(title="Math")
        self.assertEqual(c.instructor, self.teacher)

    def test_student_cannot_create_course(self):
        self.login_student()
        r = self.client.get(reverse("course_create"))
        self.assertEqual(r.status_code, 403)

    # ----- Enrollment -----
    def test_student_can_enroll(self):
        self.login_student()
        r = self.client.get(reverse("enroll", args=[self.course.id]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Enrollment.objects.filter(course=self.course, student=self.student).exists())

    def test_enroll_is_idempotent(self):
        self.login_student()
        self.client.get(reverse("enroll", args=[self.course.id]))
        self.client.get(reverse("enroll", args=[self.course.id]))
        self.assertEqual(Enrollment.objects.filter(course=self.course, student=self.student).count(), 1)

    def test_blocked_student_cannot_enroll(self):
        Block.objects.create(teacher=self.teacher, blocked=self.student)
        self.login_student()
        r = self.client.get(reverse("enroll", args=[self.course.id]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Enrollment.objects.filter(course=self.course, student=self.student).exists())
        self.assertContains(r, "blocked", status_code=200)

    # ----- Feedback -----
    def test_feedback_requires_enrollment(self):
        self.login_student()
        r = self.client.post(reverse("give_feedback", args=[self.course.id]), {"content": "Nice class"}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Feedback.objects.filter(course=self.course, student=self.student).exists())
        self.assertContains(r, "must be enrolled", status_code=200)

    def test_feedback_ok_when_enrolled(self):
        Enrollment.objects.create(course=self.course, student=self.student)
        self.login_student()
        r = self.client.post(reverse("give_feedback", args=[self.course.id]), {"content": "Great!"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Feedback.objects.filter(course=self.course, student=self.student, content="Great!").exists())

    # ----- Materials -----
    def test_material_upload_teacher_only(self):
        self.login_student()
        r = self.client.get(reverse("material_upload", args=[self.course.id]))
        self.assertEqual(r.status_code, 403)

    def test_material_upload_success(self):
        self.login_teacher()
        file_obj = SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
        r = self.client.post(
            reverse("material_upload", args=[self.course.id]),
            {"title": "Week 1", "upload": file_obj},
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Material.objects.filter(course=self.course, title="Week 1").exists())

    # ----- Status updates -----
    def test_post_status_creates_update(self):
        self.login_student()
        r = self.client.post(reverse("post_status"), {"content": "Hi there"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(StatusUpdate.objects.filter(user=self.student, content="Hi there").exists())

    # ----- Course detail shows materials + feedback -----
    def test_course_detail_lists_materials_and_feedback(self):
        # prep: one material, one feedback
        Material.objects.create(course=self.course, title="Syllabus", upload=SimpleUploadedFile("syllabus.txt", b"x"))
        Enrollment.objects.create(course=self.course, student=self.student)
        Feedback.objects.create(course=self.course, student=self.student, content="Good!")

        self.login_student()
        r = self.client.get(reverse("course_detail", args=[self.course.id]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Syllabus")
        self.assertContains(r, "Good!")
