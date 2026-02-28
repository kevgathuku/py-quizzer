import pytest
from django.core.management import call_command

from quizzer.snippetz.models import CodeSnippet, PythonVersion


@pytest.mark.django_db
class TestSeedQuizCommand:
    def test_seed_creates_versions(self):
        call_command("seed_quiz")
        assert PythonVersion.objects.count() >= 9

    def test_seed_creates_snippets(self):
        call_command("seed_quiz")
        assert CodeSnippet.objects.count() >= 10

    def test_seed_is_idempotent(self):
        call_command("seed_quiz")
        version_count = PythonVersion.objects.count()
        snippet_count = CodeSnippet.objects.count()

        call_command("seed_quiz")
        assert PythonVersion.objects.count() == version_count
        assert CodeSnippet.objects.count() == snippet_count
