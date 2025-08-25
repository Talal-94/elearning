# chat/tests_websocket.py
from asgiref.sync import async_to_sync
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase

from courses.models import Course, Enrollment
import chat.routing

User = get_user_model()

def ws_path_for_course(course_id: int) -> str:
    """
    Adjust this to match your routing.
    Default assumes: path('ws/chat/<str:room_name>/', ...)
    and you use room names like 'course_<id>'.
    """
    return f"/ws/chat/{course_id}/"


class ChatAuthTests(TransactionTestCase):
    """
    Uses TransactionTestCase because we run an event loop with Channels' communicator.
    No database rollbacks inside async context issues.
    """

    def setUp(self):
        # App under test: Channels routing with auth
        self.application = AuthMiddlewareStack(URLRouter(chat.routing.websocket_urlpatterns))

        # Users
        self.teacher = User.objects.create_user(username="teach", password="pw", role=User.TEACHER)
        self.student = User.objects.create_user(username="stud1", password="pw", role=User.STUDENT)
        self.other_student = User.objects.create_user(username="stud2", password="pw", role=User.STUDENT)

        # Course + enrollment
        self.course = Course.objects.create(title="Web Dev", description="CM3035", instructor=self.teacher)
        Enrollment.objects.create(student=self.student, course=self.course)

        self.path = ws_path_for_course(self.course.id)

    # ---------- helpers ----------
    def _connect_as(self, user) -> bool:
        async def _inner():
            comm = WebsocketCommunicator(self.application, self.path)
            # Bypass session/cookies by injecting user into scope
            comm.scope["user"] = user
            connected, _ = await comm.connect()
            if connected:
                await comm.disconnect()
            return connected
        return async_to_sync(_inner)()

    # ---------- tests ----------
    def test_anonymous_is_rejected(self):
        anon = AnonymousUser()
        connected = self._connect_as(anon)
        self.assertFalse(connected, "Anonymous users should not be able to connect to chat")

    def test_instructor_can_connect(self):
        connected = self._connect_as(self.teacher)
        self.assertTrue(connected, "Course instructor should be allowed into their course chat")

    def test_enrolled_student_can_connect(self):
        connected = self._connect_as(self.student)
        self.assertTrue(connected, "Enrolled student should be allowed into the course chat")

    def test_unenrolled_student_is_rejected(self):
        connected = self._connect_as(self.other_student)
        self.assertFalse(connected, "Unenrolled student should not be allowed into the course chat")

    def test_other_teacher_is_rejected(self):
        other_teacher = User.objects.create_user(username="t2", password="pw", role=User.TEACHER)
        connected = self._connect_as(other_teacher)
        self.assertFalse(connected, "A different teacher must not access this course chat")
