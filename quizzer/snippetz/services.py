import logging
import random
from dataclasses import dataclass, replace

from result import Err, Ok, Result

from quizzer.snippetz.models import CodeSnippet, PythonVersion

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QuizState:
    """Immutable quiz state. All transformations return new instances."""

    question_ids: tuple[int, ...]
    choices: dict[str, list[int]]
    answers: dict[str, int]

    def next_unanswered_id(self) -> Result[int, str]:
        for sid in self.question_ids:
            if str(sid) not in self.answers:
                return Ok(sid)
        return Err("All questions answered")

    def is_finished(self) -> bool:
        return len(self.answers) == len(self.question_ids)

    @property
    def current_question_number(self) -> int:
        return len(self.answers) + 1

    def record_answer(self, snippet_id: int, answer_id: int) -> "QuizState":
        return replace(
            self,
            answers={**self.answers, str(snippet_id): answer_id},
        )


NUM_CHOICES = 4


class QuizSession:
    """Thin IO boundary for reading/writing QuizState to Django sessions."""

    def __init__(self, request):
        self.session = request.session

    def load(self) -> Result[QuizState, str]:
        data = self.session.get("quiz")
        if not data:
            logger.debug("load: no quiz data in session")
            return Err("No active quiz")
        return Ok(
            QuizState(
                question_ids=tuple(data["question_ids"]),
                choices=data["choices"],
                answers=data["answers"],
            )
        )

    def save(self, state: QuizState) -> None:
        self.session["quiz"] = {
            "question_ids": list(state.question_ids),
            "choices": state.choices,
            "answers": state.answers,
        }

    def create_quiz(self, num_questions=5) -> QuizState:
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
            if len(other_versions) >= NUM_CHOICES - 1:
                other_versions = random.sample(other_versions, NUM_CHOICES - 1)
            choice_version_pks = [correct.pk] + [v.pk for v in other_versions]
            choices_by_snippet[str(snippet_id)] = choice_version_pks

        state = QuizState(
            question_ids=tuple(snippet_ids),
            choices=choices_by_snippet,
            answers={},
        )
        self.save(state)
        return state

    def fetch_next_snippet(self, state: QuizState) -> Result[CodeSnippet, str]:
        match state.next_unanswered_id():
            case Ok(snippet_id):
                return Ok(
                    CodeSnippet.objects.select_related("first_appearance").get(
                        pk=snippet_id
                    )
                )
            case Err() as err:
                return err

    def get_choices_for_snippet(self, state: QuizState, snippet) -> list:
        choice_version_pks = state.choices.get(str(snippet.pk))

        if choice_version_pks is None:
            logger.warning(
                "get_choices_for_snippet: no stored choices for snippet %d, sampling random",
                snippet.pk,
            )
            return self._sample_random_choices(snippet)

        versions = PythonVersion.objects.in_bulk()
        missing = [pk for pk in choice_version_pks if pk not in versions]
        if missing:
            logger.warning(
                "get_choices_for_snippet: version pks %s not found in db for snippet %d",
                missing,
                snippet.pk,
            )
        choices = [versions[pk] for pk in choice_version_pks if pk in versions]
        return sorted(choices, key=lambda v: (v.major, v.minor))

    def _sample_random_choices(self, snippet):
        correct = snippet.first_appearance
        others = list(
            PythonVersion.objects.exclude(pk=correct.pk).order_by("?")[
                : NUM_CHOICES - 1
            ]
        )
        return sorted([correct] + others, key=lambda v: (v.major, v.minor))

    def calculate_score(self, state: QuizState) -> dict:
        breakdown = []
        score = 0
        snippets = CodeSnippet.objects.select_related("first_appearance").in_bulk(
            list(state.question_ids)
        )
        versions = PythonVersion.objects.in_bulk()

        for snippet_id in state.question_ids:
            snippet = snippets[snippet_id]
            user_answer_id = state.answers.get(str(snippet_id))
            user_answer = versions.get(user_answer_id) if user_answer_id else None
            if user_answer_id and not user_answer:
                logger.warning(
                    "calculate_score: answer_id %s for snippet %d not found in db",
                    user_answer_id,
                    snippet_id,
                )
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
            "total": len(state.question_ids),
            "breakdown": breakdown,
        }

    def reset(self):
        if "quiz" in self.session:
            del self.session["quiz"]
