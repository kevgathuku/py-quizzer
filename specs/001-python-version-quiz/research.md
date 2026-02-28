# Research: Python Version Quiz

**Date**: 2026-02-28
**Status**: Complete — no NEEDS CLARIFICATION items

## Decisions

### R-001: Database — SQLite in all environments

- **Decision**: Use SQLite for development and production
- **Rationale**: Application serves modest traffic with a single
  administrator. SQLite eliminates the need for a database server,
  simplifies deployment, and aligns with the 18+ month low-maintenance
  goal. Django's ORM abstracts the database layer, so switching later
  is straightforward if needed.
- **Alternatives considered**: PostgreSQL (production) — rejected per
  user clarification; adds operational complexity without benefit at
  this scale

### R-002: Session storage — Django default (database-backed)

- **Decision**: Use Django's default database-backed sessions
- **Rationale**: Built-in, no additional dependencies. Session data is
  minimal (list of IDs + answer dict). Database-backed sessions work
  well with SQLite for modest traffic. Cookie-based sessions would
  expose quiz state to the client.
- **Alternatives considered**: Cookie-based sessions — rejected because
  session data would be visible/tamperable client-side. Redis/Memcached
  — rejected as unnecessary operational complexity

### R-003: Code syntax validation — ast.parse

- **Decision**: Validate code snippets using Python's built-in
  `ast.parse()` in the model's `clean()` method
- **Rationale**: Standard library, no dependencies, validates syntax
  at the model level before persistence. Aligns with Constitution
  Principle IV (Strong Model Validation).
- **Alternatives considered**: External linters (flake8, pylint) —
  rejected as overkill for syntax-only validation. Manual review —
  rejected as error-prone

### R-004: Version ordering — numeric fields

- **Decision**: Model Python versions as separate `major` and `minor`
  integer fields with `ordering = ["major", "minor"]`
- **Rationale**: Semantic ordering works correctly (3.9 < 3.10)
  without string parsing. `unique_together` prevents duplicates.
  Works correctly on SQLite.
- **Alternatives considered**: Single string field (e.g., "3.10") —
  rejected because string sorting gives wrong order (3.10 < 3.9).
  Single decimal field — rejected because 3.10 == 3.1 as float

### R-005: Static files — WhiteNoise

- **Decision**: Serve static files via WhiteNoise middleware
- **Rationale**: No separate web server (nginx) needed. Single-process
  deployment with Gunicorn. Aligns with simplicity principle and
  VPS deployment target.
- **Alternatives considered**: nginx proxy — rejected as unnecessary
  complexity for this scale. Django's built-in staticfiles — not
  suitable for production

### R-006: Quiz randomization — database-level random ordering

- **Decision**: Use `order_by('?')` for random snippet selection
- **Rationale**: Simple, built-in Django ORM feature. With a small
  dataset (tens of snippets), performance is not a concern. SQLite
  supports random ordering natively.
- **Alternatives considered**: Python-level `random.sample()` on
  all IDs — viable but adds an extra query. Pre-generated quiz
  pools — over-engineered for this use case
