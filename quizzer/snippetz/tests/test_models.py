import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from quizzer.snippetz.models import CodeSnippet, PythonVersion


@pytest.mark.django_db
class TestPythonVersion:
    def test_create_version(self):
        version = PythonVersion.objects.create(major=3, minor=10)
        assert version.major == 3
        assert version.minor == 10

    def test_str_representation(self):
        version = PythonVersion.objects.create(major=3, minor=10)
        assert str(version) == "3.10"

    def test_ordering_semantic(self):
        """3.9 must come before 3.10 (not alphabetic sorting)."""
        v310 = PythonVersion.objects.create(major=3, minor=10)
        v39 = PythonVersion.objects.create(major=3, minor=9)
        v20 = PythonVersion.objects.create(major=2, minor=0)

        versions = list(PythonVersion.objects.all())
        assert versions == [v20, v39, v310]

    def test_unique_constraint(self):
        PythonVersion.objects.create(major=3, minor=10)
        with pytest.raises(IntegrityError):
            PythonVersion.objects.create(major=3, minor=10)


@pytest.mark.django_db
class TestCodeSnippet:
    @pytest.fixture
    def version(self):
        return PythonVersion.objects.create(major=3, minor=10)

    def test_create_with_valid_syntax(self, version):
        snippet = CodeSnippet(
            title="Walrus operator",
            code="(x := 10)",
            first_appearance=version,
        )
        snippet.full_clean()
        snippet.save()
        assert snippet.pk is not None

    def test_invalid_syntax_raises_error(self, version):
        snippet = CodeSnippet(
            title="Bad code",
            code="def (invalid:",
            first_appearance=version,
        )
        with pytest.raises(ValidationError, match="Invalid Python syntax"):
            snippet.full_clean()

    def test_protect_prevents_version_deletion(self, version):
        CodeSnippet.objects.create(
            title="Test snippet",
            code="x = 1",
            first_appearance=version,
        )
        from django.db.models import ProtectedError

        with pytest.raises(ProtectedError):
            version.delete()

    def test_line_ending_normalization(self, version):
        snippet = CodeSnippet(
            title="CRLF test",
            code="x = 1\r\ny = 2\r\n",
            first_appearance=version,
        )
        snippet.save()
        snippet.refresh_from_db()
        assert "\r" not in snippet.code
        assert snippet.code == "x = 1\ny = 2\n"

    def test_indentation_preserved(self, version):
        code = "def foo():\n    return 42\n"
        snippet = CodeSnippet(
            title="Indented code",
            code=code,
            first_appearance=version,
        )
        snippet.save()
        snippet.refresh_from_db()
        assert snippet.code == code
