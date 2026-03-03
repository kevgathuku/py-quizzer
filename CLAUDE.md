# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django web application — a Python Version Quiz that displays code snippets and asks users to identify the earliest Python version that can run them. Anonymous sessions, no login, no DRF, no SPA, no heavy JS.

## Tech Stack

- Python 3.14+ / Django 6.0
- SQLite (local development), PostgreSQL (production via `DATABASE_URL`)
- pytest + pytest-django (testing, 80%+ coverage required)
- Gunicorn + WhiteNoise (deployment)

## Commands

```bash
# All commands use uv as the Python tooling interface
uv run python manage.py runserver
uv run python manage.py makemigrations
uv run python manage.py migrate

# Testing (TDD is mandatory)
uv run pytest
uv run pytest --cov=quizzer --cov-fail-under=80
uv run pytest quizzer/snippetz/tests/test_models.py  # single test file
uv run pytest -k test_name                            # single test

# Dependencies
uv add <package>                                      # add production dep
uv add --dev <package>                                # add dev dep

# Data seeding (idempotent)
uv run python manage.py seed_quiz

# Environment
# direnv auto-activates .venv via .envrc
```

## Architecture

**MVT with service layer** — all business logic lives in `services.py`, views are thin wrappers.

- `quizzer/` — Django project config (settings, urls, wsgi)
- `quizzer/snippetz/` — Main app (registered as `quizzer.snippetz` in INSTALLED_APPS)
  - models, views, services, admin, management commands
  - `tests/` — test package with `test_models.py`, `test_services.py`, `test_views.py`, `test_integration.py`
  - `templates/snippetz/` — Django templates

### Key Models

- **PythonVersion** — `major`/`minor` fields, semantic ordering, `UniqueConstraint`
- **CodeSnippet** — `title`, `code` (syntax-validated via `ast.parse`), `first_appearance` FK (PROTECT), `explanation`

### Session Design

Minimal deterministic state stored in Django sessions:
- `question_ids`: ordered list of snippet IDs
- `answers`: dict mapping snippet_id → chosen version_id
- All derived state (current question, score, finished) computed dynamically — never stored

### Service Layer (`services.py`)

`QuizSession` wrapper class handles: `create_quiz()`, `fetch_next_snippet()`, `get_choices_for_snippet()`, `calculate_score()`. `QuizState` is an immutable dataclass with `next_unanswered_id()`, `is_finished()`, `record_answer()`. No business logic in views or templates.

### Routes (URL namespace: `quiz:`)

- `GET /quiz/start/` (`quiz:start`) — start a new quiz
- `GET /quiz/question/` (`quiz:question`) — display current question
- `POST /quiz/question/` (`quiz:question`) — submit answer
- `GET /quiz/results/` (`quiz:results`) — show results
- `GET /` (`home`) — landing page

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
- `specs/001-python-version-quiz/` — feature spec, plan, tasks, data model, contracts
- `.specify/memory/constitution.md` — project constitution (6 core principles)
