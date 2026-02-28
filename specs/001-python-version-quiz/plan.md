# Implementation Plan: Python Version Quiz

**Branch**: `001-python-version-quiz` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-python-version-quiz/spec.md`

## Summary

Build a Django web application that presents Python code snippets and asks anonymous users to identify the earliest Python version supporting each snippet. The application uses server-rendered templates, Django sessions for state, a service layer for all business logic, and SQLite throughout. TDD is mandatory with 80%+ coverage.

## Technical Context

**Language/Version**: Python 3.12+ / Django 6.0+
**Primary Dependencies**: Django, Gunicorn, WhiteNoise
**Storage**: SQLite (all environments)
**Testing**: pytest + pytest-django, coverage >= 80%
**Target Platform**: Linux VPS
**Project Type**: Web service (server-rendered, no SPA)
**Performance Goals**: Pages load in under 1 second for modest concurrent users
**Constraints**: No DRF, no SPA, no heavy JS, no login for quiz-takers
**Scale/Scope**: Modest traffic, 2 models, 4 pages, 1 admin interface, 1 management command

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-First | PASS | TDD order specified: Models → Services → Views → Integration. Coverage target 80%+ (SC-006) |
| II. Thin Views, Fat Services | PASS | QuizSession service class handles all business logic. Views delegate to services |
| III. Deterministic State | PASS | Session stores only question_ids and answers dict. Score, current question, finished state all derived (FR-004) |
| IV. Strong Model Validation | PASS | ast.parse syntax validation on CodeSnippet, PROTECT on FK, unique_together on PythonVersion (FR-005, FR-006, FR-009) |
| V. Simplicity & Restraint | PASS | No login, no API, no SPA, no heavy JS, no leaderboards, no timers. Explicit out-of-scope list |
| VI. Production Readiness | PASS | Gunicorn + WhiteNoise, env-based config, idempotent seed command, SQLite in all environments (SC-007) |

**Gate result**: PASS — no violations, no complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-python-version-quiz/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── routes.md        # URL contract
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
quizzer/                          # Django project config
├── settings.py
├── urls.py
├── wsgi.py
└── snippetz/                     # Main Django app
    ├── models.py                 # PythonVersion, CodeSnippet
    ├── services.py               # QuizSession wrapper
    ├── views.py                  # Thin views delegating to services
    ├── urls.py                   # App URL patterns
    ├── forms.py                  # Answer submission form
    ├── admin.py                  # Admin with monospace textarea
    ├── apps.py                   # App config
    ├── templates/
    │   └── snippetz/
    │       ├── start.html        # Quiz start page
    │       ├── question.html     # Question display + answer form
    │       ├── results.html      # Score + per-question breakdown
    │       └── no_snippets.html  # Empty database message
    ├── management/
    │   └── commands/
    │       └── seed_quiz.py      # Idempotent seed command
    ├── migrations/
    └── tests/
        ├── __init__.py
        ├── test_models.py        # Model tests
        ├── test_services.py      # Service layer tests
        ├── test_views.py         # View tests
        └── test_integration.py   # Full flow integration tests
```

**Structure Decision**: Standard Django project layout. Single app (`snippetz`) nested under the project config directory (`quizzer/`). This matches the existing skeleton already generated. No frontend/backend split needed — server-rendered templates only.

## Complexity Tracking

> No violations — table not needed.
