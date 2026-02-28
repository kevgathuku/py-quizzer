import random

from quizzer.snippetz.models import CodeSnippet, PythonVersion


class QuizSession:
    NUM_CHOICES = 4

    def __init__(self, request):
        self.session = request.session

    def _get_data(self):
        return self.session.get("quiz")

    def start(self, num_questions=5):
        snippet_ids = list(
            CodeSnippet.objects.order_by("?").values_list("pk", flat=True)[
                :num_questions
            ]
        )
        snippets = CodeSnippet.objects.select_related("first_appearance").in_bulk(
            snippet_ids
        )
        all_versions = list(PythonVersion.objects.all())

        choices_by_snippet = {}
        for snippet_id in snippet_ids:
            snippet = snippets[snippet_id]
            correct = snippet.first_appearance
            other_versions = [v for v in all_versions if v.pk != correct.pk]
            if len(other_versions) >= self.NUM_CHOICES - 1:
                other_versions = random.sample(other_versions, self.NUM_CHOICES - 1)
            choice_version_pks = [correct.pk] + [v.pk for v in other_versions]
            choices_by_snippet[str(snippet_id)] = choice_version_pks

        self.session["quiz"] = {
            "question_ids": snippet_ids,
            "answers": {},
            "choices": choices_by_snippet,
        }

    def get_current_snippet(self):
        session_data = self._get_data()
        if not session_data:
            return None
        for snippet_id in session_data["question_ids"]:
            if str(snippet_id) not in session_data["answers"]:
                return CodeSnippet.objects.select_related("first_appearance").get(
                    pk=snippet_id
                )
        return None

    def submit_answer(self, snippet_id, user_choice):
        session_data = self._get_data()
        if not session_data:
            return
        session_data["answers"][str(snippet_id)] = user_choice
        self.session.modified = True

    def is_finished(self):
        session_data = self._get_data()
        if not session_data:
            return False
        return len(session_data["answers"]) == len(session_data["question_ids"])

    def calculate_score(self):
        session_data = self._get_data()
        if not session_data:
            return {"score": 0, "total": 0, "breakdown": []}

        breakdown = []
        score = 0
        snippets = CodeSnippet.objects.select_related("first_appearance").in_bulk(
            session_data["question_ids"]
        )
        versions = PythonVersion.objects.in_bulk()

        for snippet_id in session_data["question_ids"]:
            snippet = snippets[snippet_id]
            user_version_id = session_data["answers"].get(str(snippet_id))
            user_answer = versions.get(user_version_id) if user_version_id else None
            is_correct = user_version_id == snippet.first_appearance_id
            if is_correct:
                score += 1
            breakdown.append(
                {
                    "snippet": snippet,
                    "user_answer": user_answer,
                    "correct_answer": snippet.first_appearance,
                    "is_correct": is_correct,
                }
            )

        return {
            "score": score,
            "total": len(session_data["question_ids"]),
            "breakdown": breakdown,
        }

    def get_choices_for_snippet(self, snippet):
        session_data = self._get_data()
        if not session_data:
            return []

        choice_version_pks = session_data["choices"].get(str(snippet.pk), [])
        versions = PythonVersion.objects.in_bulk()
        choices = [versions[pk] for pk in choice_version_pks if pk in versions]
        return sorted(choices, key=lambda v: (v.major, v.minor))

    def reset(self):
        if "quiz" in self.session:
            del self.session["quiz"]
