from django import template
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

register = template.Library()


@register.filter
def pygmentize(code):
    return mark_safe(highlight(code, PythonLexer(), HtmlFormatter()))
