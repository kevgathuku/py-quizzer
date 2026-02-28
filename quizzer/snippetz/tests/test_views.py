import pytest
from django.test import Client

from quizzer.snippetz.models import CodeSnippet, PythonVersion


@pytest.fixture
def versions(db):
    return [
        PythonVersion.objects.create(major=3, minor=6),
        PythonVersion.objects.create(major=3, minor=8),
        PythonVersion.objects.create(major=3, minor=10),
    ]


@pytest.fixture
def snippets(versions):
    result = []
    for i in range(6):
        result.append(
            CodeSnippet.objects.create(
                title=f"Snippet {i + 1}",
                code=f"x = {i + 1}",
                first_appearance=versions[i % len(versions)],
            )
        )
    return result


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
class TestStartView:
    def test_start_redirects_to_question(self, client, snippets):
        response = client.get("/quiz/start/")
        assert response.status_code == 302
        assert response.url == "/quiz/question/"

    def test_start_with_no_snippets_renders_no_snippets(self, client):
        response = client.get("/quiz/start/")
        assert response.status_code == 200
        assert "no_snippets" in response.templates[0].name

    def test_start_with_fewer_than_5_uses_all(self, client, versions):
        CodeSnippet.objects.create(
            title="Only one", code="x = 1", first_appearance=versions[0]
        )
        response = client.get("/quiz/start/")
        assert response.status_code == 302
        session = client.session
        assert len(session["quiz"]["question_ids"]) == 1


@pytest.mark.django_db
class TestQuestionView:
    def test_question_renders_with_snippet(self, client, snippets):
        client.get("/quiz/start/")
        response = client.get("/quiz/question/")
        assert response.status_code == 200
        assert "snippet" in response.context
        assert "versions" in response.context

    def test_question_redirects_to_start_without_session(self, client):
        response = client.get("/quiz/question/")
        assert response.status_code == 302
        assert response.url == "/quiz/start/"

    def test_post_answer_redirects(self, client, snippets):
        client.get("/quiz/start/")
        session = client.session
        snippet_id = session["quiz"]["question_ids"][0]
        version = PythonVersion.objects.first()

        response = client.post(
            "/quiz/question/",
            {"version_id": version.pk},
        )
        assert response.status_code == 302


@pytest.mark.django_db
class TestResultsView:
    def _complete_quiz(self, client, snippets):
        """Start and answer all questions."""
        client.get("/quiz/start/")
        session = client.session
        snippet_map = {s.pk: s for s in snippets}
        for qid in session["quiz"]["question_ids"]:
            version = snippet_map[qid].first_appearance
            client.post("/quiz/question/", {"version_id": version.pk})

    def test_results_renders_with_score(self, client, snippets):
        self._complete_quiz(client, snippets)
        response = client.get("/quiz/results/")
        assert response.status_code == 200
        assert "score" in response.context
        assert "breakdown" in response.context

    def test_results_redirects_if_not_finished(self, client, snippets):
        client.get("/quiz/start/")
        response = client.get("/quiz/results/")
        assert response.status_code == 302
        assert response.url == "/quiz/question/"

    def test_results_redirects_if_no_quiz(self, client):
        response = client.get("/quiz/results/")
        assert response.status_code == 302
        assert response.url == "/quiz/start/"

    def test_restart_clears_session(self, client, snippets):
        self._complete_quiz(client, snippets)
        old_ids = client.session["quiz"]["question_ids"]
        client.get("/quiz/start/")
        new_ids = client.session["quiz"]["question_ids"]
        # New quiz should exist (may or may not have same IDs due to randomness)
        assert len(new_ids) == 5
