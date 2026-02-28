# Python Version Quiz

A Django web app that tests your knowledge of Python version history. You're shown code snippets and asked to identify the earliest Python version that supports each one.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
# Install dependencies
uv sync

# Run migrations
uv run python manage.py migrate

# Seed quiz content (10 snippets covering Python 2.7 through 3.10)
uv run python manage.py seed_quiz
```

## Running the App

```bash
uv run python manage.py runserver
```

Visit http://localhost:8000/ to start a quiz.

## How It Works

1. **Start** — Visit the homepage. A quiz of 5 random snippets is created and stored in your session.
2. **Answer** — For each snippet, pick the Python version you think first introduced the feature.
3. **Results** — After all 5 questions, see your score with a per-question breakdown: your answer, the correct answer, and an explanation of the feature.
4. **Restart** — Click "Take Another Quiz" to start fresh with a new random set.

## Available Interfaces

### Web UI

| URL | Description |
|-----|-------------|
| `/` | Redirects to quiz start |
| `/quiz/start/` | Starts a new quiz session |
| `/quiz/question/` | Shows the current question |
| `/quiz/results/` | Shows score and per-question breakdown |

### Admin Panel

Manage versions and snippets at `/admin/`.

```bash
# Create an admin account first
uv run python manage.py createsuperuser
```

From the admin you can:
- Add, edit, or remove Python versions
- Add, edit, or remove code snippets (with syntax validation and a monospace editor)

### Seed Command

Populate the database with built-in content:

```bash
uv run python manage.py seed_quiz
```

This creates 9 Python versions (2.7 through 3.10) and 10 code snippets covering features like f-strings, the walrus operator, and pattern matching. The command is idempotent — running it multiple times won't create duplicates.

## Adding Content Manually

You can add your own snippets through the admin panel or the Django shell:

```bash
uv run python manage.py shell
```

```python
from quizzer.snippetz.models import PythonVersion, CodeSnippet

version, _ = PythonVersion.objects.get_or_create(major=3, minor=12)
CodeSnippet.objects.create(
    title="Type Parameter Syntax",
    code="type Point[T] = tuple[T, T]",
    first_appearance=version,
    explanation="PEP 695 introduced type parameter syntax in Python 3.12.",
)
```

Code snippets are validated with `ast.parse()` on save, so only valid Python syntax is accepted.

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=quizzer.snippetz --cov-report=term-missing

# Run a specific test file
uv run pytest quizzer/snippetz/tests/test_models.py
```

## Production

The app uses SQLite and WhiteNoise for static files, so no external services are needed.

```bash
export DJANGO_SECRET_KEY="your-secret-key"
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS="yourdomain.com"

uv run python manage.py collectstatic --noinput
uv run python manage.py migrate
uv run python manage.py seed_quiz
uv run gunicorn quizzer.wsgi:application --bind 0.0.0.0:8000
```
