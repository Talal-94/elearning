from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from courses.models import Course

User = get_user_model()

class ChatViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user("t1", "t@example.com", "x", role=User.TEACHER)
        self.student = User.objects.create_user("s1", "s@example.com", "x", role=User.STUDENT)
        self.course = Course.objects.create(title="Chat101", description="desc", instructor=self.teacher)

    def test_room_requires_login(self):
        url = reverse("chat_room", args=[self.course.id])
        r = self.client.get(url)

        self.assertEqual(r.status_code, 302)

