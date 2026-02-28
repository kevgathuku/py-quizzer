<!--
Sync Impact Report
- Version change: N/A → 1.0.0 (initial ratification)
- Added principles: I. Test-First, II. Thin Views Fat Services,
  III. Deterministic State, IV. Strong Model Validation,
  V. Simplicity & Restraint, VI. Production Readiness
- Added sections: Technical Constraints, Development Workflow
- Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ compatible (Constitution Check section exists)
  - .specify/templates/spec-template.md: ✅ compatible (no changes needed)
  - .specify/templates/tasks-template.md: ✅ compatible (TDD order supported)
  - CLAUDE.md: ✅ aligned (reflects same principles)
- Follow-up TODOs: None
-->

# Python Version Quiz Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

- TDD MUST be followed: write tests, confirm they fail, then implement
- Testing order MUST follow: Models → Services → Views → Integration
- Automated test coverage MUST reach at least 80%
- CI MUST fail below the coverage threshold
- Integration tests MUST simulate complete user flows
  (start quiz → answer all questions → validate score → reset)

### II. Thin Views, Fat Services

- All business logic MUST live in the service layer
- Views MUST only coordinate request/response and delegate to services
- Templates MUST NOT contain business logic or data transformation
- The service layer MUST be fully testable independent of views
- Session mutations MUST be centralized in the service layer

### III. Deterministic State

- Session storage MUST be minimal: only store raw user inputs
  (snippet IDs and selected answers)
- Computed values (current question, score, finished state)
  MUST be derived dynamically — never stored
- State derivation rules:
  - Current question = first unanswered snippet
  - Finished = all snippets answered
  - Score = count of correct answers

### IV. Strong Model Validation

- Data integrity MUST be enforced at the model level, not in views
  or services
- Code snippets MUST be validated for syntactic correctness before
  persistence
- Referential integrity MUST prevent deletion of referenced entities
  (e.g., a Python version in use by snippets)
- Uniqueness constraints MUST prevent duplicate records
  (e.g., duplicate major.minor version pairs)
- Line endings MUST be normalized; indentation MUST be preserved
  exactly as entered

### V. Simplicity & Restraint

- No features beyond what is explicitly specified — YAGNI applies
- No login system for quiz-takers
- No REST API, no API framework
- No single-page application patterns
- No heavyweight JavaScript frameworks or rich editors
- The project MUST remain small and maintainable for 18+ months
  without attention
- When in doubt, choose the simpler approach

### VI. Production Readiness

- Application MUST be deployable to a VPS with documented steps
- Configuration (debug mode, secret key, allowed hosts) MUST come
  from the environment
- Static files MUST be served without a separate web server in
  front of the application
- A management command MUST seed initial content idempotently
- All migrations MUST run cleanly on a fresh database
- SQLite MUST be used in all environments including production

## Technical Constraints

- Python 3.12+
- Django 6.0+
- SQLite in all environments (development and production)
- pytest + pytest-django for testing
- Gunicorn for WSGI serving
- WhiteNoise for static file serving
- No DRF, no SPA frontend, no heavy JavaScript

## Development Workflow

- TDD order: Models → Services → Views → Integration
- Commit after each logical unit of work
- Use `select_related` for foreign key queries
- Code displayed in `<pre><code>` to preserve formatting
- Admin interface: monospace textarea, no JavaScript editors,
  list display of title/version/created_at
- Seed command MUST be idempotent and safe to run repeatedly

## Governance

- This constitution supersedes all other development practices
  for this project
- Amendments require updating this file, incrementing the version,
  and propagating changes to dependent templates
- All implementation work MUST verify compliance with these
  principles before merging
- Complexity beyond these principles MUST be justified in the
  plan's Complexity Tracking table
- See `CLAUDE.md` for runtime development guidance

**Version**: 1.0.0 | **Ratified**: 2026-02-28 | **Last Amended**: 2026-02-28
