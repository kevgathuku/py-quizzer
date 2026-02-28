import pytest
from django.test import RequestFactory

from quizzer.snippetz.models import CodeSnippet, PythonVersion
from quizzer.snippetz.services import QuizSession


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


@pytest.mark.django_db
class TestQuizSessionStart:
    def test_start_creates_session_with_question_ids(
        self, request_with_session, snippets
    ):
        quiz = QuizSession(request_with_session)
        quiz.start()
        data = request_with_session.session.get("quiz")
        assert data is not None
        assert "question_ids" in data
        assert len(data["question_ids"]) == 5

    def test_start_creates_empty_answers(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        quiz.start()
        data = request_with_session.session["quiz"]
        assert data["answers"] == {}

    def test_start_with_fewer_than_default_snippets(
        self, request_with_session, versions
    ):
        # Only 2 snippets exist
        CodeSnippet.objects.create(
            title="S1", code="a = 1", first_appearance=versions[0]
        )
        CodeSnippet.objects.create(
            title="S2", code="b = 2", first_appearance=versions[1]
        )
        quiz = QuizSession(request_with_session)
        quiz.start()
        data = request_with_session.session["quiz"]
        assert len(data["question_ids"]) == 2


@pytest.mark.django_db
class TestQuizSessionProgression:
    def test_get_current_snippet_returns_first_unanswered(
        self, request_with_session, snippets
    ):
        quiz = QuizSession(request_with_session)
        quiz.start()
        first_id = request_with_session.session["quiz"]["question_ids"][0]
        current = quiz.get_current_snippet()
        assert current.pk == first_id

    def test_submit_answer_stores_correctly(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        quiz.start()
        question_ids = request_with_session.session["quiz"]["question_ids"]
        snippet_id = question_ids[0]
        version_id = snippets[0].first_appearance_id

        quiz.submit_answer(snippet_id, version_id)

        answers = request_with_session.session["quiz"]["answers"]
        assert str(snippet_id) in answers
        assert answers[str(snippet_id)] == version_id

    def test_current_advances_after_answer(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        quiz.start()
        question_ids = request_with_session.session["quiz"]["question_ids"]

        quiz.submit_answer(question_ids[0], snippets[0].first_appearance_id)
        current = quiz.get_current_snippet()
        assert current.pk == question_ids[1]

    def test_is_finished_false_when_questions_remain(
        self, request_with_session, snippets
    ):
        quiz = QuizSession(request_with_session)
        quiz.start()
        assert quiz.is_finished() is False

    def test_is_finished_true_when_all_answered(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        quiz.start()
        question_ids = request_with_session.session["quiz"]["question_ids"]
        for qid in question_ids:
            quiz.submit_answer(qid, snippets[0].first_appearance_id)
        assert quiz.is_finished() is True


@pytest.mark.django_db
class TestQuizSessionResults:
    def _answer_all(self, quiz, request_with_session, snippets):
        """Answer all questions with correct answers."""
        question_ids = request_with_session.session["quiz"]["question_ids"]
        snippet_map = {s.pk: s for s in snippets}
        for qid in question_ids:
            snippet = snippet_map[qid]
            quiz.submit_answer(qid, snippet.first_appearance_id)

    def test_calculate_score_correct_count(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        quiz.start()
        self._answer_all(quiz, request_with_session, snippets)
        result = quiz.calculate_score()
        assert result["score"] == result["total"]

    def test_calculate_score_with_wrong_answers(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        quiz.start()
        question_ids = request_with_session.session["quiz"]["question_ids"]
        wrong_version = PythonVersion.objects.create(major=1, minor=0)
        for qid in question_ids:
            quiz.submit_answer(qid, wrong_version.pk)
        result = quiz.calculate_score()
        assert result["score"] == 0
        assert result["total"] == len(question_ids)

    def test_calculate_score_breakdown_has_is_correct(
        self, request_with_session, snippets
    ):
        quiz = QuizSession(request_with_session)
        quiz.start()
        self._answer_all(quiz, request_with_session, snippets)
        result = quiz.calculate_score()
        assert len(result["breakdown"]) == result["total"]
        for item in result["breakdown"]:
            assert "is_correct" in item
            assert "snippet" in item
            assert "user_answer" in item
            assert "correct_answer" in item

    def test_reset_clears_session(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        quiz.start()
        quiz.reset()
        assert request_with_session.session.get("quiz") is None


@pytest.mark.django_db
class TestQuizSessionChoices:
    def test_choices_always_includes_correct_answer(
        self, request_with_session, snippets
    ):
        quiz = QuizSession(request_with_session)
        snippet = snippets[0]
        choices = quiz.get_choices_for_snippet(snippet)
        assert snippet.first_appearance in choices

    def test_choices_limited_to_4(self, request_with_session, snippets, versions):
        # Ensure more than 4 versions exist
        PythonVersion.objects.create(major=3, minor=11)
        PythonVersion.objects.create(major=3, minor=12)
        quiz = QuizSession(request_with_session)
        snippet = snippets[0]
        choices = quiz.get_choices_for_snippet(snippet)
        assert len(choices) == 4

    def test_choices_returns_all_when_fewer_than_4(self, request_with_session, db):
        v1 = PythonVersion.objects.create(major=3, minor=6)
        v2 = PythonVersion.objects.create(major=3, minor=8)
        snippet = CodeSnippet.objects.create(
            title="Test", code="x = 1", first_appearance=v1
        )
        quiz = QuizSession(request_with_session)
        choices = quiz.get_choices_for_snippet(snippet)
        assert choices == [v1, v2]

    def test_choices_ordered_by_version(self, request_with_session, snippets):
        quiz = QuizSession(request_with_session)
        snippet = snippets[0]
        choices = quiz.get_choices_for_snippet(snippet)
        version_tuples = [(v.major, v.minor) for v in choices]
        assert version_tuples == sorted(version_tuples)
