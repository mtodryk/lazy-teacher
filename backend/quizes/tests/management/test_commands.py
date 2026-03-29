from django.core.management import call_command
from django.test import TestCase
from io import StringIO
from django.contrib.auth.models import User
from quizes.models import Quiz, QuizSubmission
from documents.models import Document

class ManagementCommandsTest(TestCase):
    def test_test_count(self):
        user = User.objects.create_user("a", "a@example.com", "pass")
        document = Document.objects.create(user=user, title="t", file_name="f", status=Document.Status.READY, chunk_count=1)
        Quiz.objects.create(user=user, document=document, code="c1")
        out = StringIO()
        call_command("test_count", stdout=out)
        assert "Total quizes created: 1" in out.getvalue()

    def test_users_count(self):
        User.objects.create_user("x", "x@example.com", "pass")
        out = StringIO()
        call_command("users_count", stdout=out)
        assert "Total registered users: 1" in out.getvalue()