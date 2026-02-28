import ast

from django.core.exceptions import ValidationError
from django.db import models


class PythonVersion(models.Model):
    major = models.PositiveSmallIntegerField()
    minor = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["major", "minor"]
        unique_together = ("major", "minor")

    def __str__(self):
        return f"{self.major}.{self.minor}"


class CodeSnippet(models.Model):
    title = models.CharField(max_length=200)
    code = models.TextField()
    first_appearance = models.ForeignKey(
        PythonVersion,
        on_delete=models.PROTECT,
    )
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        try:
            ast.parse(self.code)
        except SyntaxError as e:
            raise ValidationError(f"Invalid Python syntax: {e}")

    def save(self, *args, **kwargs):
        self.code = self.code.replace("\r\n", "\n").replace("\r", "\n")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
