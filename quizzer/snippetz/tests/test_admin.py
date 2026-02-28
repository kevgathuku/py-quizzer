import pytest
from django.contrib.admin.sites import AdminSite

from quizzer.snippetz.admin import CodeSnippetAdmin
from quizzer.snippetz.models import CodeSnippet, PythonVersion


@pytest.mark.django_db
class TestAdmin:
    def test_models_registered(self):
        from django.contrib.admin.sites import site

        assert PythonVersion in site._registry
        assert CodeSnippet in site._registry

    def test_snippet_admin_uses_monospace_textarea(self):
        admin = CodeSnippetAdmin(CodeSnippet, AdminSite())
        form_class = admin.get_form(None)
        form = form_class()
        widget = form.fields["code"].widget
        assert "monospace" in widget.attrs.get("style", "")

    def test_admin_rejects_invalid_syntax(self):
        version = PythonVersion.objects.create(major=3, minor=10)
        admin = CodeSnippetAdmin(CodeSnippet, AdminSite())
        form_class = admin.get_form(None)
        form = form_class(
            data={
                "title": "Bad",
                "code": "def (invalid:",
                "first_appearance": version.pk,
                "explanation": "",
            }
        )
        assert not form.is_valid()
