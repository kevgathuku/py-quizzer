# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django web application — a Python Version Quiz that displays code snippets and asks users to identify the earliest Python version that can run them. Anonymous sessions, no login, no DRF, no SPA, no heavy JS.

## Tech Stack

- Python 3.12+ / Django 6.0
- SQLite (all environments, including production)
- pytest + pytest-django (testing, 80%+ coverage required)
- Gunicorn + WhiteNoise (deployment)

## Commands

```bash
# Development
python manage.py runserver
python manage.py makemigrations
python manage.py migrate

# Testing (TDD is mandatory)
pytest
pytest --cov=quizzer --cov-fail-under=80
pytest quizzer/snippetz/tests/test_models.py        # single test file
pytest -k test_name                                  # single test

# Data seeding (idempotent)
python manage.py seed_quiz

# Environment
# direnv auto-activates .venv via .envrc
```

## Architecture

**MVT with service layer** — all business logic lives in `services.py`, views are thin wrappers.

- `quizzer/` — Django project config (settings, urls, wsgi)
- `quizzer/snippetz/` — Main app: models, views, services, admin, management commands

### Key Models

- **PythonVersion** — `major`/`minor` fields, semantic ordering, `unique_together`
- **CodeSnippet** — `title`, `code` (syntax-validated via `ast.parse`), `first_appearance` FK (PROTECT), `explanation`

### Session Design

Minimal deterministic state stored in Django sessions:
- `question_ids`: ordered list of snippet IDs
- `answers`: dict mapping snippet_id → chosen version_id
- All derived state (current question, score, finished) computed dynamically — never stored

### Service Layer (`services.py`)

`QuizSession` wrapper class handles: `start()`, `get_current_snippet()`, `submit_answer()`, `is_finished()`, `calculate_score()`, `reset()`. No business logic in views or templates.

### Routes

- `GET /quiz/start/` — start a new quiz
- `GET /quiz/question/` — display current question
- `POST /quiz/question/` — submit answer
- `GET /quiz/results/` — show results

## Design Constraints

- No business logic in views or templates
- Model-level validation (syntax checking via `ast.parse`)
- Use `select_related` for FK queries
- Code rendered in `<pre><code>` to preserve indentation
- Admin: monospace textarea, no JS editors, list display of title/version/created_at

## TDD Order

Models → Services → Views → Integration (full quiz flow)

## Specs

- `docs/specfiication_v0.md` — detailed Django specification
- `specs/001-python-version-quiz/` — feature specification

## Active Technologies
- Python 3.12+ / Django 6.0+ + Django, Gunicorn, WhiteNoise (001-python-version-quiz)
- SQLite (all environments) (001-python-version-quiz)

## Recent Changes
- 001-python-version-quiz: Added Python 3.12+ / Django 6.0+ + Django, Gunicorn, WhiteNoise
