import pytest
from django.test import RequestFactory

from quizzer.snippetz.models import CodeSnippet, PythonVersion
from quizzer.snippetz.services import QuizSession, QuizState


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
            choices={"1": [10], "2": [10], "3": [10]},
            answers={"1": 10},
        )
        assert state.next_unanswered_id().ok() == 2

    def test_next_unanswered_id_returns_err_when_all_answered(self):
        state = QuizState(
            question_ids=(1, 2),
            choices={"1": [10], "2": [10]},
            answers={"1": 10, "2": 10},
        )
        result = state.next_unanswered_id()
        assert result.is_err()
        assert result.err() == "All questions answered"

    def test_is_finished_false_when_questions_remain(self):
        state = QuizState(
            question_ids=(1, 2),
            choices={"1": [10], "2": [10]},
            answers={"1": 10},
        )
        assert state.is_finished() is False

    def test_is_finished_true_when_all_answered(self):
        state = QuizState(
            question_ids=(1, 2),
            choices={"1": [10], "2": [10]},
            answers={"1": 10, "2": 10},
        )
        assert state.is_finished() is True

    def test_current_question_number(self):
        state = QuizState(
            question_ids=(1, 2, 3),
            choices={"1": [10], "2": [10], "3": [10]},
            answers={"1": 10},
        )
        assert state.current_question_number == 2

    def test_record_answer_returns_new_state(self):
        state = QuizState(
            question_ids=(1, 2),
            choices={"1": [10], "2": [10]},
            answers={},
        )
        new_state = state.record_answer(1, 10)
        assert new_state is not state
        assert new_state.answers == {"1": 10}
        assert state.answers == {}  # original unchanged

    def test_record_answer_preserves_existing_answers(self):
        state = QuizState(
            question_ids=(1, 2),
            choices={"1": [10], "2": [10]},
            answers={"1": 10},
        )
        new_state = state.record_answer(2, 20)
        assert new_state.answers == {"1": 10, "2": 20}


@pytest.mark.django_db
class TestQuizSessionStart:
    def test_start_creates_state_with_question_ids(
        self, request_with_session, snippets
    ):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        assert state is not None
        assert len(state.question_ids) == 5
        assert state.answers == {}

    def test_start_saves_to_session(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        quiz.create_quiz()
        assert request_with_session.session.get("quiz") is not None

    def test_start_with_fewer_than_default_snippets(
        self, request_with_session, versions
    ):
        CodeSnippet.objects.create(
            title="S1", code="a = 1", first_appearance=versions[0]
        )
        CodeSnippet.objects.create(
            title="S2", code="b = 2", first_appearance=versions[1]
        )
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        assert len(state.question_ids) == 2


@pytest.mark.django_db
class TestQuizSessionProgression:
    def test_fetch_next_snippet_returns_first_unanswered(
        self, request_with_session, snippets
    ):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        result = quiz.fetch_next_snippet(state)
        assert result.is_ok()
        assert result.ok().pk == state.question_ids[0]

    def test_record_answer_stores_correctly(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        snippet_id = state.question_ids[0]
        user_choice = snippets[0].first_appearance_id

        new_state = state.record_answer(snippet_id, user_choice)
        quiz.save(new_state)

        loaded = quiz.load().ok()
        assert str(snippet_id) in loaded.answers
        assert loaded.answers[str(snippet_id)] == user_choice

    def test_current_advances_after_answer(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()

        state = state.record_answer(
            state.question_ids[0], snippets[0].first_appearance_id
        )
        quiz.save(state)
        state = quiz.load().ok()
        current = quiz.fetch_next_snippet(state).ok()
        assert current.pk == state.question_ids[1]

    def test_is_finished_false_when_questions_remain(
        self, request_with_session, snippets
    ):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        assert state.is_finished() is False

    def test_is_finished_true_when_all_answered(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        for qid in state.question_ids:
            state = state.record_answer(qid, snippets[0].first_appearance_id)
        assert state.is_finished() is True


@pytest.mark.django_db
class TestQuizSessionResults:
    def _answer_all(self, state, snippets):
        snippet_map = {s.pk: s for s in snippets}
        for qid in state.question_ids:
            snippet = snippet_map[qid]
            state = state.record_answer(qid, snippet.first_appearance_id)
        return state

    def test_calculate_score_correct_count(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        state = self._answer_all(state, snippets)
        result = quiz.calculate_score(state)
        assert result["score"] == result["total"]

    def test_calculate_score_with_wrong_answers(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        wrong_version = PythonVersion.objects.create(major=1, minor=0)
        for qid in state.question_ids:
            state = state.record_answer(qid, wrong_version.pk)
        result = quiz.calculate_score(state)
        assert result["score"] == 0
        assert result["total"] == len(state.question_ids)

    def test_calculate_score_breakdown_has_is_correct(
        self, request_with_session, snippets
    ):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        state = self._answer_all(state, snippets)
        result = quiz.calculate_score(state)
        assert len(result["breakdown"]) == result["total"]
        for item in result["breakdown"]:
            assert "is_correct" in item
            assert "snippet" in item
            assert "user_answer" in item
            assert "correct_answer" in item



@pytest.mark.django_db
class TestQuizSessionChoices:
    def test_choices_always_includes_correct_answer(
        self, request_with_session, snippets
    ):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        for snippet_id in state.question_ids:
            snippet = CodeSnippet.objects.select_related("first_appearance").get(
                pk=snippet_id
            )
            choices = quiz.get_choices_for_snippet(state, snippet)
            assert snippet.first_appearance in choices

    def test_choices_limited_to_4(self, request_with_session, snippets, versions):
        PythonVersion.objects.create(major=3, minor=11)
        PythonVersion.objects.create(major=3, minor=12)
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        snippet_id = state.question_ids[0]
        snippet = CodeSnippet.objects.get(pk=snippet_id)
        choices = quiz.get_choices_for_snippet(state, snippet)
        assert len(choices) == 4

    def test_choices_returns_all_when_fewer_than_4(self, request_with_session, db):
        v1 = PythonVersion.objects.create(major=3, minor=6)
        v2 = PythonVersion.objects.create(major=3, minor=8)
        snippet = CodeSnippet.objects.create(
            title="Test", code="x = 1", first_appearance=v1
        )
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        choices = quiz.get_choices_for_snippet(state, snippet)
        assert choices == [v1, v2]

    def test_choices_ordered_by_version(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        snippet = snippets[0]
        choices = quiz.get_choices_for_snippet(state, snippet)
        version_tuples = [(v.major, v.minor) for v in choices]
        assert version_tuples == sorted(version_tuples)

    def test_choices_stable_across_calls(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        state = quiz.create_quiz()
        snippet = snippets[0]
        first_call = quiz.get_choices_for_snippet(state, snippet)
        second_call = quiz.get_choices_for_snippet(state, snippet)
        assert first_call == second_call

    def test_get_choices_handles_missing_choices_key(
        self, request_with_session, snippets
    ):
        request_with_session.session["quiz"] = {
            "question_ids": [s.pk for s in snippets[:5]],
            "answers": {},
            "choices": {},
        }
        quiz = QuizSession(request_with_session)
        state = quiz.load().ok()
        snippet = snippets[0]
        choices = quiz.get_choices_for_snippet(state, snippet)
        assert len(choices) > 0
