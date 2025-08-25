from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from courses.models import Course, Enrollment

User = get_user_model()

class ApiSmokeTests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="t1", password="pw", role=User.TEACHER, email="t1@example.com")
        self.student = User.objects.create_user(username="s1", password="pw", role=User.STUDENT, email="s1@example.com")

    def test_me_endpoint(self):
        self.client.login(username="t1", password="pw")
        resp = self.client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "t1")
        self.assertEqual(resp.data["role"], User.TEACHER)

    def test_teacher_can_create_course_student_cannot(self):
        self.client.login(username="s1", password="pw")
        r = self.client.post("/api/courses/", {"title": "X", "description": "Y"})
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

        self.client.logout(); self.client.login(username="t1", password="pw")
        r = self.client.post("/api/courses/", {"title": "X", "description": "Y"})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        course_id = r.data["id"]

        t2 = User.objects.create_user(username="t2", password="pw", role=User.TEACHER, email="t2@example.com")
        c2 = APIClient(); c2.login(username="t2", password="pw")
        r2 = c2.patch(f"/api/courses/{course_id}/", {"title": "Z"})
        self.assertEqual(r2.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_enroll_and_feedback_rules(self):
        self.client.login(username="t1", password="pw")
        r = self.client.post("/api/courses/", {"title": "C", "description": "D"})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        course_id = r.data["id"]

        self.client.logout(); self.client.login(username="s1", password="pw")
        r2 = self.client.post("/api/enrollments/", {"course": course_id})
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.data["student"]["username"], "s1")

        r3 = self.client.post("/api/feedbacks/", {"course": course_id, "content": "Great!"})
        self.assertEqual(r3.status_code, status.HTTP_201_CREATED)

        self.client.logout(); self.client.login(username="t1", password="pw")
        r4 = self.client.post("/api/feedbacks/", {"course": course_id, "content": "Nice"})
        self.assertEqual(r4.status_code, status.HTTP_403_FORBIDDEN)
