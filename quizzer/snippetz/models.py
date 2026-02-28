import ast

from django.core.exceptions import ValidationError
from django.db import models


class PythonVersion(models.Model):
    """Represents a Python version (e.g., 3.10, 3.11).

    Uses semantic ordering (major, minor) and enforces uniqueness
    on the (major, minor) pair.
    """

    major = models.PositiveSmallIntegerField()
    minor = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["major", "minor"]
        unique_together = ("major", "minor")

    def __str__(self):
        return f"{self.major}.{self.minor}"


class CodeSnippet(models.Model):
    """A Python code snippet used as a quiz question.

    The first_appearance field indicates the earliest Python version
    that can run this code. Code is validated for Python syntax
    on save.
    """

    title = models.CharField(max_length=200)
    code = models.TextField()
    first_appearance = models.ForeignKey(
        PythonVersion,
        on_delete=models.PROTECT,
    )
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validate that the code is valid Python syntax."""
        try:
            ast.parse(self.code)
        except SyntaxError as e:
            raise ValidationError(f"Invalid Python syntax: {e}")

    def save(self, *args, **kwargs):
        """Normalize line endings before saving."""
        self.code = self.code.replace("\r\n", "\n").replace("\r", "\n")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
