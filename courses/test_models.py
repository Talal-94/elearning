from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from courses.models import Course, Enrollment, Material, Feedback, StatusUpdate

User = get_user_model()

class CourseModelStrTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user("t1", "t@example.com", "x", role=User.TEACHER)
        self.student = User.objects.create_user("s1", "s@example.com", "x", role=User.STUDENT)
        self.course = Course.objects.create(title="Physics", description="desc", instructor=self.teacher)

    def test_course_str(self):
        self.assertIn("Physics", str(self.course))

    def test_enrollment_str(self):
        e = Enrollment.objects.create(course=self.course, student=self.student)
        es = str(e)
        self.assertIn("Physics", es)
        self.assertIn("s1", es)

    def test_material_str(self):
        m = Material.objects.create(
            course=self.course, title="Week1",
            upload=SimpleUploadedFile("w1.txt", b"hello", content_type="text/plain"),
        )
        ms = str(m)
        self.assertIn("Week1", ms)

    def test_feedback_str(self):
        f = Feedback.objects.create(course=self.course, student=self.student, content="Great")
        fs = str(f)
        self.assertIn("s1", fs)
        self.assertIn("Physics", fs)

    def test_statusupdate_str(self):
        su = StatusUpdate.objects.create(user=self.student, content="Hi")
        self.assertIn("s1", str(su))
