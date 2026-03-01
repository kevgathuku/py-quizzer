import pytest
from django.test import Client

from quizzer.snippetz.models import CodeSnippet, PythonVersion


@pytest.fixture
def seeded_db(db):
    from django.core.management import call_command

    call_command("seed_quiz", stdout=open("/dev/null", "w"))


@pytest.mark.django_db
class TestFullQuizFlow:
    def test_complete_quiz_end_to_end(self, seeded_db):
        client = Client()

        # Start quiz
        response = client.get("/quiz/start/")
        assert response.status_code == 302
        assert response.url == "/quiz/question/"

        session = client.session
        question_ids = session["quiz"]["question_ids"]
        assert len(question_ids) == 5

        # Answer all questions
        for _ in range(5):
            response = client.get("/quiz/question/")
            assert response.status_code == 200
            snippet = response.context["snippet"]

            # Answer with the correct version
            response = client.post(
                "/quiz/question/",
                {"answer_id": snippet.first_appearance_id},
            )
            assert response.status_code == 302

        # Check results
        response = client.get("/quiz/results/")
        assert response.status_code == 200
        assert response.context["score"] == 5
        assert response.context["total"] == 5
        assert len(response.context["breakdown"]) == 5

    def test_root_redirects_to_start(self, seeded_db):
        client = Client()
        response = client.get("/")
        assert response.status_code == 302
        assert response.url == "/quiz/start/"

    def test_admin_accessible(self, seeded_db):
        from django.urls import reverse

        client = Client()
        url = reverse("admin:index")
        response = client.get(url)
        # Redirects to login (302) since we're not authenticated
        assert response.status_code == 302
        assert "/admin/login/" in response.url
