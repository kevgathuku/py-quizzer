Python Version Quiz – Django Specification
1. Objective

Build a production-ready Django application that:

Displays Python code snippets.

Asks the user to identify the earliest Python version that can run the snippet.

Uses anonymous sessions (no login).

Enforces strict TDD.

Is deployable to production.

Requires minimal long-term maintenance.

Demonstrates strong Django fundamentals and architectural clarity.

No DRF. No SPA frontend. No heavy JavaScript frameworks.

2. Tech Stack

Python 3.12+

Django 5+

SQLite (development)

PostgreSQL (production)

Gunicorn

WhiteNoise

pytest + pytest-django

Coverage ≥ 80%

3. Folder structure - already exists

4. Domain Model
4.1 PythonVersion

Proper semantic modeling (no string sorting issues).

class LanguageVersion(models.Model):
    major = models.PositiveSmallIntegerField()
    minor = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["major", "minor"]
        unique_together = ("major", "minor")

    def __str__(self):
        return f"{self.major}.{self.minor}"
Requirements

Semantic ordering must work correctly.

Cannot duplicate versions.

Must work correctly on Sqlite.

4.2 CodeSnippet
class CodeSnippet(models.Model):
    title = models.CharField(max_length=200)
    code = models.TextField()
    first_appearance = models.ForeignKey(
        PythonVersion,
        on_delete=models.PROTECT
    )
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        import ast
        from django.core.exceptions import ValidationError

        try:
            ast.parse(self.code)
        except SyntaxError as e:
            raise ValidationError(f"Invalid Python syntax: {e}")
Requirements

on_delete=PROTECT must prevent deleting a version in use.

Syntax must be validated at the model level.

Do not auto-strip indentation.

Normalize line endings to \n only.

Store raw source exactly as entered.

5. Session Architecture
5.1 Session Data Structure

Only store minimal deterministic state:

{
    "quiz": {
        "question_ids": [1, 5, 7, 9, 3],
        "answers": {
            "1": 4,
            "5": 6
        }
    }
}
Rules

Do NOT store score.

Do NOT store current index.

Derive all state dynamically.

Current question = first unanswered snippet.

Finished = len(answers) == len(question_ids).

Score = count of correct answers.

6. Service Layer

All business logic must live in services.py.

6.1 QuizSession Wrapper
class QuizSession:
    def __init__(self, request):
        ...
    def start(self, num_questions=5):
        ...
    def get_current_snippet(self):
        ...
    def submit_answer(self, snippet_id, version_id):
        ...
    def is_finished(self):
        ...
    def calculate_score(self):
        ...
    def reset(self):
        ...
Requirements

No business logic in views.

Session mutations centralized.

Must be fully testable independently of views.

7. Views

Endpoints:

GET /quiz/start/

GET /quiz/question/

POST /quiz/question/

GET /quiz/results/

Rules

Views must be thin.

No business logic in templates.

Use select_related for efficiency.

Render code inside <pre><code> to preserve indentation.

8. Admin Interface
8.1 Custom Admin Form

Use large monospace textarea.

Validate syntax.

Normalize line endings only.

widgets = {
    "code": forms.Textarea(
        attrs={
            "rows": 25,
            "style": "font-family: monospace;"
        }
    )
}
Requirements

No heavy JS editor.

No CodeMirror.

Keep maintenance minimal.

Admin must show list display of title, version, created_at.

9. Management Command

Provide:

python manage.py seed_quiz
Requirements

Idempotent.

Safe to run multiple times.

Creates:

Python versions (1.09 minimum).

At least 10 realistic snippets.

Must not duplicate records.

10. TDD Requirements (Mandatory Order)
10.1 Model Tests

Version creation

Version ordering

Unique constraint

PROTECT works

Snippet syntax validation

Snippet invalid syntax raises error

10.2 Service Tests

Starting quiz creates session

Question progression works

Submitting answer stores correctly

Score calculated correctly

Finished state correct

Reset clears session

10.3 View Tests

Start endpoint works

Question page renders

POST answer redirects correctly

Results page shows correct score

10.4 Full Flow Integration Test

Simulate:

Start quiz

Answer all questions

Validate final score

Confirm reset works

Coverage Requirement

Minimum 80%.

CI must fail below threshold.

11. Deployment Requirements
11.1 Production Settings

DEBUG from environment

SECRET_KEY from environment

DATABASE_URL support

ALLOWED_HOSTS configurable

Secure SSL proxy header

Production logging configured

11.2 Static Files

WhiteNoise configured

collectstatic works

11.3 WSGI
gunicorn pyquiz.wsgi:application

All migrations run cleanly.

11.5 Deployment Target

VPS

Must include documented deployment steps.

12. Non-Functional Constraints

No login system.

No REST API.

No DRF.

No SPA frontend.

No heavy JS.

No leaderboard.

No timers.

No unnecessary features.

The project must remain small and low maintenance.

13. Definition of Done

The project is complete when:

All tests pass.

Coverage ≥ 80%.

Runs locally.

Deploys successfully.

Simple sqlite in production.

Session-based quiz works end-to-end.

No manual database manipulation required.

Seed command works idempotently.

14. Design Principles to Enforce

Deterministic state.

Minimal session storage.

Strong model-level validation.

Thin views.

Clear service abstraction.

Correct semantic version modeling.

Deployment realism.

Operational maturity (management command).

Maintainable for 18+ months without attention.

15. What This Project Must Signal

Strong Django fundamentals.

Proper domain modeling.

Respect for Python semantics.

Clean architecture.

Testing discipline.

Production awareness.

Restraint and clarity.

No overengineering.

No gimmicks.