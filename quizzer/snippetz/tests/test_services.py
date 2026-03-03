import pytest
from django.test import RequestFactory

from quizzer.snippetz.models import CodeSnippet, PythonVersion
from quizzer.snippetz.services import (
    QuizSession,
    QuizState,
    calculate_score,
    create_quiz,
    fetch_next_question,
    get_choices_for_question,
    submit_answer,
)


@pytest.fixture
def versions(db):
    return [
        PythonVersion.objects.create(major=2, minor=7),
        PythonVersion.objects.create(major=3, minor=6),
        PythonVersion.objects.create(major=3, minor=8),
        PythonVersion.objects.create(major=3, minor=10),
    ]


@pytest.fixture
def snippets(versions):
    return [
        CodeSnippet.objects.create(
            title=f"Snippet {i + 1}",
            code=f"{'x' if i < 4 else 'y'} = {i + 1}",
            first_appearance=versions[i % len(versions)],
        )
        for i in range(8)
    ]


@pytest.fixture
def request_with_session():
    factory = RequestFactory()
    request = factory.get("/")
    from django.contrib.sessions.backends.db import SessionStore

    request.session = SessionStore()
    return request


class TestQuizState:
    def test_next_unanswered_id_returns_first_unanswered(self):
        state = QuizState(
            question_ids=(1, 2, 3),
            choices={1: [10], 2: [10], 3: [10]},
            answers={1: 10},
        )
        assert state.next_unanswered_id().ok() == 2

    def test_next_unanswered_id_returns_err_when_all_answered(self):
        state = QuizState(
            question_ids=(1, 2),
            choices={1: [10], 2: [10]},
            answers={1: 10, 2: 10},
        )
        result = state.next_unanswered_id()
        assert result.is_err()
        assert result.err() == "All questions answered"

    def test_is_finished_false_when_questions_remain(self):
        state = QuizState(
            question_ids=(1, 2),
            choices={1: [10], 2: [10]},
            answers={1: 10},
        )
        assert state.is_finished() is False

    def test_is_finished_true_when_all_answered(self):
        state = QuizState(
            question_ids=(1, 2),
            choices={1: [10], 2: [10]},
            answers={1: 10, 2: 10},
        )
        assert state.is_finished() is True

    def test_current_question_number(self):
        state = QuizState(
            question_ids=(1, 2, 3),
            choices={1: [10], 2: [10], 3: [10]},
            answers={1: 10},
        )
        assert state.current_question_number == 2

    def test_record_answer_returns_new_state(self):
        state = QuizState(
            question_ids=(1, 2),
            choices={1: [10], 2: [10]},
            answers={},
        )
        new_state = state.record_answer(1, 10)
        assert new_state is not state
        assert new_state.answers == {1: 10}
        assert state.answers == {}  # original unchanged

    def test_record_answer_preserves_existing_answers(self):
        state = QuizState(
            question_ids=(1, 2),
            choices={1: [10], 2: [20]},
            answers={1: 10},
        )
        new_state = state.record_answer(2, 20)
        assert new_state.answers == {1: 10, 2: 20}


@pytest.mark.django_db
class TestCreateQuiz:
    def test_creates_state_with_question_ids(self, snippets):
        state = create_quiz()
        assert len(state.question_ids) == 5
        assert state.answers == {}

    def test_with_fewer_than_default_snippets(self, versions):
        CodeSnippet.objects.create(
            title="S1", code="a = 1", first_appearance=versions[0]
        )
        CodeSnippet.objects.create(
            title="S2", code="b = 2", first_appearance=versions[1]
        )
        state = create_quiz()
        assert len(state.question_ids) == 2


@pytest.mark.django_db
class TestQuizSessionIO:
    def test_save_and_load_round_trip(self, request_with_session, snippets):
        session = QuizSession(request_with_session)
        state = create_quiz()
        session.save(state)

        loaded = session.load().ok()
        assert loaded.question_ids == state.question_ids
        assert loaded.choices == state.choices
        assert loaded.answers == state.answers

    def test_load_returns_err_without_session_data(self, request_with_session):
        session = QuizSession(request_with_session)
        result = session.load()
        assert result.is_err()

    def test_save_persists_answers(self, request_with_session, snippets):
        session = QuizSession(request_with_session)
        state = create_quiz()
        question_id = state.question_ids[0]
        user_choice = snippets[0].first_appearance_id

        state = state.record_answer(question_id, user_choice)
        session.save(state)

        loaded = session.load().ok()
        assert question_id in loaded.answers
        assert loaded.answers[question_id] == user_choice


@pytest.mark.django_db
class TestSubmitAnswer:
    def _valid_choice(self, state):
        """Return a valid choice ID for the first unanswered question."""
        question_id = state.next_unanswered_id().ok()
        return state.choices[question_id][0]

    def test_records_answer_for_next_unanswered(self, snippets):
        state = create_quiz()
        first_id = state.question_ids[0]
        choice = self._valid_choice(state)
        result = submit_answer(state, choice)
        assert result.is_ok()
        assert result.ok().answers[first_id] == choice

    def test_returns_err_when_all_answered(self, snippets):
        state = create_quiz()
        for qid in state.question_ids:
            state = state.record_answer(qid, state.choices[qid][0])
        result = submit_answer(state, 99)
        assert result.is_err()

    def test_advances_to_next_question(self, snippets):
        state = create_quiz()
        choice = self._valid_choice(state)
        new_state = submit_answer(state, choice).ok()
        assert new_state.next_unanswered_id().ok() == state.question_ids[1]

    def test_rejects_answer_not_in_choices(self, snippets):
        state = create_quiz()
        result = submit_answer(state, 999999)
        assert result.is_err()
        assert "Invalid answer" in result.err()


@pytest.mark.django_db
class TestFetchNextQuestion:
    def test_returns_first_unanswered(self, snippets):
        state = create_quiz()
        result = fetch_next_question(state)
        assert result.is_ok()
        assert result.ok().pk == state.question_ids[0]

    def test_advances_after_answer(self, snippets):
        state = create_quiz()
        state = state.record_answer(
            state.question_ids[0], snippets[0].first_appearance_id
        )
        current = fetch_next_question(state).ok()
        assert current.pk == state.question_ids[1]


@pytest.mark.django_db
class TestQuizProgression:
    def test_is_finished_false_when_questions_remain(self, snippets):
        state = create_quiz()
        assert state.is_finished() is False

    def test_is_finished_true_when_all_answered(self, snippets):
        state = create_quiz()
        for qid in state.question_ids:
            state = state.record_answer(qid, snippets[0].first_appearance_id)
        assert state.is_finished() is True


@pytest.mark.django_db
class TestCalculateScore:
    def _answer_all(self, state, snippets):
        snippet_map = {s.pk: s for s in snippets}
        for qid in state.question_ids:
            snippet = snippet_map[qid]
            state = state.record_answer(qid, snippet.first_appearance_id)
        return state

    def test_correct_count(self, snippets):
        state = create_quiz()
        state = self._answer_all(state, snippets)
        result = calculate_score(state)
        assert result["score"] == result["total"]

    def test_with_wrong_answers(self, snippets):
        state = create_quiz()
        wrong_version = PythonVersion.objects.create(major=1, minor=0)
        for qid in state.question_ids:
            state = state.record_answer(qid, wrong_version.pk)
        result = calculate_score(state)
        assert result["score"] == 0
        assert result["total"] == len(state.question_ids)

    def test_breakdown_has_expected_keys(self, snippets):
        state = create_quiz()
        state = self._answer_all(state, snippets)
        result = calculate_score(state)
        assert len(result["breakdown"]) == result["total"]
        for item in result["breakdown"]:
            assert "is_correct" in item
            assert "snippet" in item
            assert "user_answer" in item
            assert "correct_answer" in item


@pytest.mark.django_db
class TestGetChoicesForQuestion:
    def test_always_includes_correct_answer(self, snippets):
        state = create_quiz()
        for question_id in state.question_ids:
            snippet = CodeSnippet.objects.select_related("first_appearance").get(
                pk=question_id
            )
            choices = get_choices_for_question(state, snippet)
            assert snippet.first_appearance in choices

    def test_limited_to_4(self, snippets, versions):
        PythonVersion.objects.create(major=3, minor=11)
        PythonVersion.objects.create(major=3, minor=12)
        state = create_quiz()
        question_id = state.question_ids[0]
        snippet = CodeSnippet.objects.get(pk=question_id)
        choices = get_choices_for_question(state, snippet)
        assert len(choices) == 4

    def test_returns_all_when_fewer_than_4(self, db):
        v1 = PythonVersion.objects.create(major=3, minor=6)
        v2 = PythonVersion.objects.create(major=3, minor=8)
        snippet = CodeSnippet.objects.create(
            title="Test", code="x = 1", first_appearance=v1
        )
        state = create_quiz()
        choices = get_choices_for_question(state, snippet)
        assert choices == [v1, v2]

    def test_ordered_by_version(self, snippets):
        state = create_quiz()
        snippet = snippets[0]
        choices = get_choices_for_question(state, snippet)
        version_tuples = [(v.major, v.minor) for v in choices]
        assert version_tuples == sorted(version_tuples)

    def test_stable_across_calls(self, snippets):
        state = create_quiz()
        snippet = snippets[0]
        first_call = get_choices_for_question(state, snippet)
        second_call = get_choices_for_question(state, snippet)
        assert first_call == second_call

    def test_handles_missing_choices_key(self, request_with_session, snippets):
        request_with_session.session["quiz"] = {
            "question_ids": [s.pk for s in snippets[:5]],
            "answers": {},
            "choices": {},
        }
        session = QuizSession(request_with_session)
        state = session.load().ok()
        snippet = snippets[0]
        choices = get_choices_for_question(state, snippet)
        assert len(choices) > 0
