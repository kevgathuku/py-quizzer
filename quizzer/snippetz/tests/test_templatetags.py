from django.template import Context, Template

import pytest


@pytest.mark.django_db
class TestPygmentizeFilter:
    def test_produces_highlighted_html(self):
        template = Template("{% load pygments_tags %}{{ code|pygmentize }}")
        result = template.render(Context({"code": "x = 1"}))
        assert '<div class="highlight">' in result
        assert "<pre>" in result

    def test_highlights_python_keywords(self):
        template = Template("{% load pygments_tags %}{{ code|pygmentize }}")
        result = template.render(Context({"code": "def foo():\n    pass"}))
        assert "<span" in result

    def test_empty_code(self):
        template = Template("{% load pygments_tags %}{{ code|pygmentize }}")
        result = template.render(Context({"code": ""}))
        assert '<div class="highlight">' in result
