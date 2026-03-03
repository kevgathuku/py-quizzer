from django import forms
from django.contrib import admin

from quizzer.snippetz.models import CodeSnippet, PythonVersion


class CodeSnippetAdminForm(forms.ModelForm):
    class Meta:
        model = CodeSnippet
        fields = "__all__"
        widgets = {
            "code": forms.Textarea(
                attrs={"style": "font-family: monospace; width: 80ch; height: 20em;"}
            ),
        }


@admin.register(PythonVersion)
class PythonVersionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "major", "minor")


@admin.register(CodeSnippet)
class CodeSnippetAdmin(admin.ModelAdmin):
    form = CodeSnippetAdminForm
    list_display = ("title", "first_appearance", "created_at")
    list_filter = ("first_appearance",)
