import logging

from result import Err, Ok

from django.shortcuts import redirect, render

from quizzer.snippetz.models import CodeSnippet
from quizzer.snippetz.services import (
    QuizSession,
    calculate_score,
    create_quiz,
    fetch_next_snippet,
    get_choices_for_snippet,
    submit_answer,
)

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "snippetz/start.html")


def start_quiz(request):
    if not CodeSnippet.objects.exists():
        return render(request, "snippetz/no_snippets.html")

    session = QuizSession(request)
    state = create_quiz()
    session.save(state)
    return redirect("quiz:question")


def question(request):
    session = QuizSession(request)

    match session.load():
        case Ok(state):
            pass
        case Err(e):
            logger.warning("question: unable to load state. redirecting to start: %s", e)
            return redirect("quiz:start")

    if state.is_finished():
        return redirect("quiz:results")

    if request.method == "POST":
        answer_id = request.POST.get("answer_id")
        if answer_id:
            match submit_answer(state, int(answer_id)):
                case Ok(new_state):
                    state = new_state
                    session.save(state)
                case Err(e):
                    logger.warning("question POST: could not submit answer: %s", e)
        if state.is_finished():
            return redirect("quiz:results")
        return redirect("quiz:question")

    match fetch_next_snippet(state):
        case Ok(snippet):
            versions = get_choices_for_snippet(state, snippet)
            return render(
                request,
                "snippetz/question.html",
                {
                    "snippet": snippet,
                    "versions": versions,
                    "question_number": state.current_question_number,
                    "total_questions": len(state.question_ids),
                },
            )
        case Err(e):
            logger.warning("question GET: could not fetch snippet: %s", e)
            return redirect("quiz:start")


def results(request):
    session = QuizSession(request)

    match session.load():
        case Ok(state):
            pass
        case Err(e):
            logger.warning("results: redirecting to start: %s", e)
            return redirect("quiz:start")

    if not state.is_finished():
        return redirect("quiz:question")

    result = calculate_score(state)
    return render(request, "snippetz/results.html", result)
