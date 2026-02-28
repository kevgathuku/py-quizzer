import random

from quizzer.snippetz.models import CodeSnippet, PythonVersion


class QuizSession:
    NUM_CHOICES = 4

    def __init__(self, request):
        self.session = request.session

    def _get_data(self):
        return self.session.get("quiz")

    def start(self, num_questions=5):
        ids = list(
            CodeSnippet.objects.order_by("?").values_list("pk", flat=True)[
                :num_questions
            ]
        )
        snippets = CodeSnippet.objects.select_related("first_appearance").in_bulk(ids)
        all_versions = list(PythonVersion.objects.all())

        choices = {}
        for qid in ids:
            snippet = snippets[qid]
            correct = snippet.first_appearance
            others = [v for v in all_versions if v.pk != correct.pk]
            if len(others) >= self.NUM_CHOICES - 1:
                others = random.sample(others, self.NUM_CHOICES - 1)
            choice_pks = [correct.pk] + [v.pk for v in others]
            choices[str(qid)] = choice_pks

        self.session["quiz"] = {
            "question_ids": ids,
            "answers": {},
            "choices": choices,
        }

    def get_current_snippet(self):
        data = self._get_data()
        if not data:
            return None
        for qid in data["question_ids"]:
            if str(qid) not in data["answers"]:
                return CodeSnippet.objects.select_related("first_appearance").get(
                    pk=qid
                )
        return None

    def submit_answer(self, snippet_id, user_choice):
        data = self._get_data()
        if not data:
            return
        data["answers"][str(snippet_id)] = user_choice
        self.session.modified = True

    def is_finished(self):
        data = self._get_data()
        if not data:
            return False
        return len(data["answers"]) == len(data["question_ids"])

    def calculate_score(self):
        data = self._get_data()
        if not data:
            return {"score": 0, "total": 0, "breakdown": []}

        breakdown = []
        score = 0
        snippets = CodeSnippet.objects.select_related("first_appearance").in_bulk(
            data["question_ids"]
        )
        versions = PythonVersion.objects.in_bulk()

        for qid in data["question_ids"]:
            snippet = snippets[qid]
            user_version_id = data["answers"].get(str(qid))
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
            "total": len(data["question_ids"]),
            "breakdown": breakdown,
        }

    def get_choices_for_snippet(self, snippet):
        data = self._get_data()
        if not data:
            return []

        choice_pks = data["choices"].get(str(snippet.pk), [])
        versions = PythonVersion.objects.in_bulk()
        choices = [versions[pk] for pk in choice_pks if pk in versions]
        return sorted(choices, key=lambda v: (v.major, v.minor))

    def reset(self):
        if "quiz" in self.session:
            del self.session["quiz"]
