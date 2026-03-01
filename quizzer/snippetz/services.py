import random

from quizzer.snippetz.models import CodeSnippet, PythonVersion


class QuizSession:
    """Manages quiz session state stored in Django session (no database persistence).

    Session structure:
        {
            "question_ids": [snippet_id, ...],  # ordered list of snippet PKs
            "answers": {snippet_id: answer_id, ...},  # user's answers
            "choices": {snippet_id: [answer_id, ...], ...},  # pre-generated choices
        }
    """

    NUM_CHOICES = 4

    def __init__(self, request):
        self.session = request.session

    def _get_data(self):
        """Retrieve the quiz data dict from session, or None if not started."""
        return self.session.get("quiz")

    def start(self, num_questions=5):
        """Initialize a new quiz with random snippets and choices.

        Args:
            num_questions: Number of snippets to include in the quiz (default 5).
        """
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
        """Return the next unanswered snippet, or None if quiz is complete."""
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
        """Record the user's answer for a snippet.

        Args:
            snippet_id: The PK of the CodeSnippet being answered.
            user_choice: The PK of the PythonVersion the user selected.
        """
        session_data = self._get_data()
        if not session_data:
            return
        session_data["answers"][str(snippet_id)] = user_choice
        # Must explicitly mark session as modified because we're mutating a nested dict,
        # which Django cannot detect automatically
        self.session.modified = True

    def is_finished(self):
        """Return True if all questions have been answered."""
        session_data = self._get_data()
        if not session_data:
            return False
        return len(session_data["answers"]) == len(session_data["question_ids"])

    def calculate_score(self):
        """Calculate the user's score and return a results dict.

        Returns:
            dict with keys: score (int), total (int), breakdown (list of dicts)
        """
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
            user_answer_id = session_data["answers"].get(str(snippet_id))
            user_answer = versions.get(user_answer_id) if user_answer_id else None
            is_correct = user_answer_id == snippet.first_appearance_id
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
        """Get the multiple choice options for a snippet.

        Returns stored choices from session if available, otherwise generates them.
        Choices are sorted by version number.

        Args:
            snippet: The CodeSnippet to get choices for.

        Returns:
            List of PythonVersion objects, sorted by (major, minor).
        """
        session_data = self._get_data()
        if not session_data:
            return []

        choices_data = session_data.get("choices", {})
        choice_version_pks = choices_data.get(str(snippet.pk))

        if choice_version_pks is None:
            return self._generate_choices_for_snippet(snippet)

        versions = PythonVersion.objects.in_bulk()
        choices = [versions[pk] for pk in choice_version_pks if pk in versions]
        return sorted(choices, key=lambda v: (v.major, v.minor))

    def _generate_choices_for_snippet(self, snippet):
        """Generate random choices for a snippet (fallback for old sessions)."""
        correct = snippet.first_appearance
        others = list(
            PythonVersion.objects.exclude(pk=correct.pk).order_by("?")[
                : self.NUM_CHOICES - 1
            ]
        )
        return sorted([correct] + others, key=lambda v: (v.major, v.minor))

    def reset(self):
        """Clear all quiz data from the session."""
        if "quiz" in self.session:
            del self.session["quiz"]
