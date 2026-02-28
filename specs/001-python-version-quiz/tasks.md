# Tasks: Python Version Quiz

**Input**: Design documents from `/specs/001-python-version-quiz/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: TDD is mandatory per Constitution Principle I and SC-006 (80%+ coverage). Tests are written first, verified to fail, then implementation follows.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and test configuration

- [x] T001 Register snippetz app in INSTALLED_APPS in quizzer/settings.py
- [x] T002 Install and configure pytest + pytest-django + pytest-cov in pyproject.toml
- [x] T003 Create pytest configuration (pytest.ini or pyproject.toml [tool.pytest]) with DJANGO_SETTINGS_MODULE
- [x] T004 Create test package structure at quizzer/snippetz/tests/__init__.py
- [x] T005 Configure WhiteNoise middleware in quizzer/settings.py
- [x] T006 Configure environment-based settings (SECRET_KEY, DEBUG, ALLOWED_HOSTS) in quizzer/settings.py

**Checkpoint**: Project runs, pytest discovers tests, `python manage.py check` passes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data models and migrations that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] Write PythonVersion model tests in quizzer/snippetz/tests/test_models.py: version creation, ordering (3.9 before 3.10), unique constraint, __str__ output
- [x] T008 [P] Write CodeSnippet model tests in quizzer/snippetz/tests/test_models.py: creation with valid syntax, syntax validation rejects invalid code, PROTECT prevents version deletion, line ending normalization, indentation preservation

### Implementation for Foundational

- [x] T009 Implement PythonVersion model in quizzer/snippetz/models.py: major/minor fields, unique_together, ordering, __str__
- [x] T010 Implement CodeSnippet model in quizzer/snippetz/models.py: title, code, first_appearance FK (PROTECT), explanation, created_at, clean() with ast.parse, save() with line ending normalization
- [x] T011 Generate and run migrations with `python manage.py makemigrations snippetz && python manage.py migrate`

**Checkpoint**: All model tests pass. `python manage.py migrate` runs cleanly.

---

## Phase 3: User Story 1 — Take a Quiz (Priority: P1) MVP

**Goal**: A visitor can start a quiz, answer 5 questions about Python version features, and progress through all questions

**Independent Test**: Visit start page, answer each question sequentially, verify question progression works correctly

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T012 [P] [US1] Write QuizSession service tests in quizzer/snippetz/tests/test_services.py: start() creates session with question_ids and empty answers, get_current_snippet() returns first unanswered, submit_answer() stores answer correctly, is_finished() returns False when questions remain, question progression (current advances after answer)
- [x] T013 [P] [US1] Write view tests for start and question endpoints in quizzer/snippetz/tests/test_views.py: GET /quiz/start/ redirects to /quiz/question/, GET /quiz/question/ renders question.html with snippet and versions, POST /quiz/question/ records answer and redirects, start with no snippets renders no_snippets.html, start with fewer than 5 snippets uses all available

### Implementation for User Story 1

- [x] T014 [US1] Implement QuizSession service in quizzer/snippetz/services.py: __init__(request), start(num_questions=5) with random selection, get_current_snippet() deriving current from session state, submit_answer(snippet_id, version_id), is_finished()
- [x] T015 [US1] Create answer submission form in quizzer/snippetz/forms.py: version_id field validation
- [x] T016 [US1] Implement start_quiz view in quizzer/snippetz/views.py: delegates to QuizSession.start(), handles no-snippets edge case, redirects to question
- [x] T017 [US1] Implement question view (GET + POST) in quizzer/snippetz/views.py: GET renders snippet with version choices using select_related, POST delegates to submit_answer and redirects
- [x] T018 [P] [US1] Create start.html template in quizzer/snippetz/templates/snippetz/start.html
- [x] T019 [P] [US1] Create question.html template in quizzer/snippetz/templates/snippetz/question.html: display code in `<pre><code>`, version radio buttons, question number/total
- [x] T020 [P] [US1] Create no_snippets.html template in quizzer/snippetz/templates/snippetz/no_snippets.html
- [x] T021 [US1] Create app URL configuration in quizzer/snippetz/urls.py: quiz/start/, quiz/question/
- [x] T022 [US1] Wire app URLs into project URL configuration in quizzer/urls.py: include snippetz.urls, add root redirect to /quiz/start/

**Checkpoint**: User can start a quiz, see questions one at a time, and answer all 5. All US1 tests pass.

---

## Phase 4: User Story 2 — View Results and Restart (Priority: P2)

**Goal**: After completing all questions, user sees score with per-question breakdown (their answer, correct answer, explanation) and can restart

**Independent Test**: Complete a quiz, verify results page shows correct score and breakdown, restart and confirm fresh quiz

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T023 [P] [US2] Write QuizSession results service tests in quizzer/snippetz/tests/test_services.py: calculate_score() returns correct count, calculate_score() returns per-question breakdown with is_correct flags, reset() clears session state
- [x] T024 [P] [US2] Write view tests for results endpoint in quizzer/snippetz/tests/test_views.py: GET /quiz/results/ renders results.html with score and breakdown, GET /quiz/results/ redirects to question if quiz not finished, GET /quiz/results/ redirects to start if no active quiz, restart via GET /quiz/start/ clears previous session

### Implementation for User Story 2

- [x] T025 [US2] Add calculate_score() and reset() methods to QuizSession in quizzer/snippetz/services.py: score count, per-question breakdown (snippet, user_answer, correct_answer, is_correct), reset clears quiz session data
- [x] T026 [US2] Implement results view in quizzer/snippetz/views.py: delegates to calculate_score(), renders results.html, redirects if quiz not finished or no active quiz
- [x] T027 [US2] Create results.html template in quizzer/snippetz/templates/snippetz/results.html: total score, per-question breakdown with snippet title, user's answer, correct answer, right/wrong indicator, explanation
- [x] T028 [US2] Add results URL to quizzer/snippetz/urls.py: quiz/results/

**Checkpoint**: Full quiz flow works end-to-end: start → answer all → see results with breakdown → restart. All US1 + US2 tests pass.

---

## Phase 5: User Story 3 — Manage Quiz Content (Priority: P3)

**Goal**: Administrator can manage versions and snippets via admin interface, and seed initial content via management command

**Independent Test**: Log into admin, create a version, create a snippet with valid/invalid syntax, run seed_quiz command, verify idempotency

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T029 [P] [US3] Write admin tests in quizzer/snippetz/tests/test_admin.py: admin registers PythonVersion and CodeSnippet, snippet admin uses monospace textarea for code field, admin rejects snippet with invalid syntax
- [x] T030 [P] [US3] Write seed_quiz management command tests in quizzer/snippetz/tests/test_commands.py: seed creates at least 9 PythonVersions and 10 CodeSnippets, seed is idempotent (running twice creates no duplicates)

### Implementation for User Story 3

- [x] T031 [US3] Implement admin configuration in quizzer/snippetz/admin.py: PythonVersion admin with list_display (major, minor), CodeSnippet admin with list_display (title, first_appearance, created_at), monospace textarea widget for code field, syntax validation on save
- [x] T032 [US3] Create seed_quiz management command in quizzer/snippetz/management/commands/seed_quiz.py: create Python versions (at least 2.0 through 3.12+), create at least 10 realistic code snippets with correct first_appearance versions, use get_or_create for idempotency

**Checkpoint**: Admin interface fully functional. Seed command populates data idempotently. All US3 tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integration testing, production readiness, coverage verification

- [x] T033 Write full flow integration test in quizzer/snippetz/tests/test_integration.py: start quiz → answer all questions → verify correct score on results → restart → verify fresh quiz
- [x] T034 Verify test coverage meets 80% threshold by running `pytest --cov=quizzer --cov-fail-under=80`
- [x] T035 Run quickstart.md validation: fresh migrate, seed_quiz, runserver, complete a quiz end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2
- **User Story 2 (Phase 4)**: Depends on Phase 3 (results require a completed quiz flow)
- **User Story 3 (Phase 5)**: Depends on Phase 2 only (admin/seed are independent of quiz flow)
- **Polish (Phase 6)**: Depends on Phases 3, 4, and 5

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before views
- Views before templates (though templates marked [P] can be created alongside views)
- URL config after views exist

### Parallel Opportunities

- T007 + T008: Model tests can be written in parallel
- T012 + T013: US1 service tests + view tests in parallel
- T018 + T019 + T020: US1 templates in parallel
- T023 + T024: US2 service tests + view tests in parallel
- T029 + T030: US3 admin tests + command tests in parallel
- Phase 4 (US2) and Phase 5 (US3) can run in parallel after Phase 3 completes

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (models + migrations)
3. Complete Phase 3: User Story 1 (quiz flow)
4. **STOP and VALIDATE**: User can take a quiz start-to-finish

### Incremental Delivery

1. Setup + Foundational → Models ready
2. Add User Story 1 → Quiz taking works (MVP!)
3. Add User Story 2 → Results + restart works
4. Add User Story 3 → Admin + seed works
5. Polish → Integration tests, coverage check, deployment validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- TDD is mandatory: write tests, verify they fail, then implement
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
