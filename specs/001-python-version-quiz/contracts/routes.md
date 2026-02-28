# URL Routes Contract: Python Version Quiz

**Date**: 2026-02-28

All routes are under the `/quiz/` prefix. No REST API — all
routes serve HTML pages via standard Django views.

## Routes

### GET /quiz/start/

**Purpose**: Start a new quiz session
**View behavior**:
1. Delegate to `QuizSession.start(num_questions=5)`
2. Redirect to `/quiz/question/`
**Edge cases**:
- No snippets in database → render `no_snippets.html`
- Fewer than 5 snippets → use all available

### GET /quiz/question/

**Purpose**: Display the current unanswered code snippet
**View behavior**:
1. Delegate to `QuizSession.get_current_snippet()`
2. Render `question.html` with snippet and version choices
**Context data**:
- `snippet`: current CodeSnippet (with `select_related("first_appearance")`)
- `versions`: all PythonVersion objects (semantically ordered)
- `question_number`: current position (1-based)
- `total_questions`: total quiz size
**Edge cases**:
- No active quiz → redirect to `/quiz/start/`
- Quiz finished → redirect to `/quiz/results/`

### POST /quiz/question/

**Purpose**: Submit an answer for the current snippet
**View behavior**:
1. Validate submitted version_id
2. Delegate to `QuizSession.submit_answer(snippet_id, version_id)`
3. If quiz finished → redirect to `/quiz/results/`
4. Else → redirect to `/quiz/question/`
**Form data**:
- `version_id`: integer — PK of the selected PythonVersion
**Edge cases**:
- Already-answered snippet → ignore, redirect to next question
- Invalid version_id → re-render form with error

### GET /quiz/results/

**Purpose**: Display quiz results with per-question breakdown
**View behavior**:
1. Delegate to `QuizSession.calculate_score()`
2. Render `results.html` with score and breakdown
**Context data**:
- `score`: number of correct answers
- `total`: total questions
- `breakdown`: list of dicts, each with:
  - `snippet`: CodeSnippet instance
  - `user_answer`: PythonVersion the user chose
  - `correct_answer`: PythonVersion (first_appearance)
  - `is_correct`: boolean
**Edge cases**:
- Quiz not finished → redirect to `/quiz/question/`
- No active quiz → redirect to `/quiz/start/`

### GET / (root)

**Purpose**: Landing page
**View behavior**: Redirect to `/quiz/start/`

## Admin Routes (Django built-in)

### /admin/

Standard Django admin interface with:
- PythonVersion: list display of `major`, `minor`
- CodeSnippet: list display of `title`, `first_appearance`,
  `created_at`. Monospace textarea for `code` field.
  Syntax validation on save.
