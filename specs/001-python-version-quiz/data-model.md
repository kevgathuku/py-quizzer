# Data Model: Python Version Quiz

**Date**: 2026-02-28

## Entities

### PythonVersion

Represents a Python release by major and minor version number.

| Field | Type | Constraints |
|-------|------|-------------|
| id | Auto primary key | Django default |
| major | PositiveSmallIntegerField | Required |
| minor | PositiveSmallIntegerField | Required |

**Constraints**:
- `unique_together = ("major", "minor")` — no duplicate versions
- `ordering = ["major", "minor"]` — semantic sort order
- `on_delete=PROTECT` on related CodeSnippet FK — cannot delete
  a version that has associated snippets

**Display**: `__str__` returns `"{major}.{minor}"` (e.g., "3.10")

### CodeSnippet

A Python code sample tied to the version that first introduced
the feature it demonstrates.

| Field | Type | Constraints |
|-------|------|-------------|
| id | Auto primary key | Django default |
| title | CharField(max_length=200) | Required |
| code | TextField | Required, syntax-validated |
| first_appearance | ForeignKey(PythonVersion) | Required, on_delete=PROTECT |
| explanation | TextField | Optional (blank=True) |
| created_at | DateTimeField | auto_now_add=True |

**Validation** (in `clean()` method):
- `ast.parse(self.code)` — rejects invalid Python syntax with
  a clear error message
- Line endings normalized to `\n` before saving (in `save()`)
- Indentation preserved exactly as entered — no auto-stripping

**Relationships**:
- `first_appearance` → `PythonVersion` (many-to-one)
- PROTECT prevents orphaned references

## Session State (not a database model)

Quiz state is stored in Django's session framework, not in a
database model.

```python
{
    "quiz": {
        "question_ids": [1, 5, 7, 9, 3],   # snippet PKs, ordered
        "answers": {
            "1": 4,   # snippet_id (str) → version_id (int)
            "5": 6
        }
    }
}
```

**Derivation rules** (never stored):
- Current question = first ID in `question_ids` not in `answers`
- Finished = `len(answers) == len(question_ids)`
- Score = count where `answers[snippet_id]` matches
  `snippet.first_appearance_id`

## Entity Relationship

```text
PythonVersion 1 ──────< CodeSnippet
   (major, minor)         (title, code, explanation)
                          FK: first_appearance
                          on_delete: PROTECT
```
