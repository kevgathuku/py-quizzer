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
    choices: dict[int, list[int]]
    answers: dict[int, int]

    def next_unanswered_id(self) -> Result[int, str]:
        for qid in self.question_ids:
            if qid not in self.answers:
                return Ok(qid)
        return Err("All questions answered")

    def is_finished(self) -> bool:
        return len(self.answers) == len(self.question_ids)

    @property
    def current_question_number(self) -> int:
        return len(self.answers) + 1

    def record_answer(self, question_id: int, answer_id: int) -> "QuizState":
        return replace(
            self,
            answers={**self.answers, question_id: answer_id},
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
                choices={int(k): v for k, v in data["choices"].items()},
                answers={int(k): v for k, v in data["answers"].items()},
            )
        )

    def save(self, state: QuizState) -> None:
        self.session["quiz"] = {
            "question_ids": list(state.question_ids),
            "choices": {str(k): v for k, v in state.choices.items()},
            "answers": {str(k): v for k, v in state.answers.items()},
        }


def create_quiz(num_questions=5) -> QuizState:
    question_ids = list(
        CodeSnippet.objects.order_by("?").values_list("pk", flat=True)[
            :num_questions
        ]
    )
    snippets = CodeSnippet.objects.select_related("first_appearance").in_bulk(
        question_ids
    )
    all_versions = list(PythonVersion.objects.all())

    choices_by_question = {}
    for question_id in question_ids:
        snippet = snippets[question_id]
        correct = snippet.first_appearance
        other_versions = [v for v in all_versions if v.pk != correct.pk]
        if len(other_versions) >= NUM_CHOICES - 1:
            other_versions = random.sample(other_versions, NUM_CHOICES - 1)
        choice_version_pks = [correct.pk] + [v.pk for v in other_versions]
        choices_by_question[question_id] = choice_version_pks

    return QuizState(
        question_ids=tuple(question_ids),
        choices=choices_by_question,
        answers={},
    )


def submit_answer(state: QuizState, answer_id: int) -> Result[QuizState, str]:
    match state.next_unanswered_id():
        case Ok(question_id):
            valid_choices = state.choices.get(question_id, [])
            if answer_id not in valid_choices:
                return Err(
                    f"Invalid answer {answer_id} for question {question_id}"
                )
            return Ok(state.record_answer(question_id, answer_id))
        case Err() as err:
            return err


def fetch_next_question(state: QuizState) -> Result[CodeSnippet, str]:
    match state.next_unanswered_id():
        case Ok(question_id):
            return Ok(
                CodeSnippet.objects.select_related("first_appearance").get(
                    pk=question_id
                )
            )
        case Err() as err:
            return err


def get_choices_for_question(state: QuizState, question) -> list:
    choice_version_pks = state.choices.get(question.pk)

    if choice_version_pks is None:
        logger.warning(
            "get_choices_for_question: no stored choices for question %d, sampling random",
            question.pk,
        )
        return _sample_random_choices(question)

    versions = PythonVersion.objects.in_bulk()
    missing = [pk for pk in choice_version_pks if pk not in versions]
    if missing:
        logger.warning(
            "get_choices_for_question: version pks %s not found in db for question %d",
            missing,
            question.pk,
        )
    choices = [versions[pk] for pk in choice_version_pks if pk in versions]
    return sorted(choices, key=lambda v: (v.major, v.minor))


def _sample_random_choices(question):
    correct = question.first_appearance
    others = list(
        PythonVersion.objects.exclude(pk=correct.pk).order_by("?")[
            : NUM_CHOICES - 1
        ]
    )
    return sorted([correct] + others, key=lambda v: (v.major, v.minor))


def calculate_score(state: QuizState) -> dict:
    breakdown = []
    score = 0
    snippets = CodeSnippet.objects.select_related("first_appearance").in_bulk(
        list(state.question_ids)
    )
    versions = PythonVersion.objects.in_bulk()

    for question_id in state.question_ids:
        snippet = snippets[question_id]
        user_answer_id = state.answers.get(question_id)
        user_answer = versions.get(user_answer_id) if user_answer_id else None
        if user_answer_id and not user_answer:
            logger.warning(
                "calculate_score: answer_id %s for question %d not found in db",
                user_answer_id,
                question_id,
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
