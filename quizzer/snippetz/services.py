from quizzer.snippetz.models import CodeSnippet, PythonVersion


class QuizSession:
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
        self.session["quiz"] = {
            "question_ids": ids,
            "answers": {},
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

    def submit_answer(self, snippet_id, version_id):
        data = self._get_data()
        if not data:
            return
        data["answers"][str(snippet_id)] = version_id
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

    def get_choices_for_snippet(self, snippet, num_choices=4):
        correct = snippet.first_appearance
        others = list(
            PythonVersion.objects.exclude(pk=correct.pk).order_by("?")[
                : num_choices - 1
            ]
        )
        return sorted([correct] + others, key=lambda v: (v.major, v.minor))

    def reset(self):
        if "quiz" in self.session:
            del self.session["quiz"]
