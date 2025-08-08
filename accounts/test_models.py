from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Block

User = get_user_model()

class AccountsModelStrTests(TestCase):
    def test_user_str(self):
        u = User.objects.create_user(username="alice", email="a@example.com", password="x", role=User.STUDENT)
        s = str(u)
        # Don’t overfit the exact string; just ensure it’s meaningful
        self.assertTrue("alice" in s or "a@example.com" in s)

    def test_block_str(self):
        t = User.objects.create_user(username="teach", email="t@example.com", password="x", role=User.TEACHER)
        s = User.objects.create_user(username="stud", email="s@example.com", password="x", role=User.STUDENT)
        b = Block.objects.create(teacher=t, blocked=s)
        bs = str(b)
        self.assertIn("teach", bs)
        self.assertIn("stud", bs)
