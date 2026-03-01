from result import Err, Ok

from django.shortcuts import redirect, render

from quizzer.snippetz.models import CodeSnippet
from quizzer.snippetz.services import QuizSession


def start_quiz(request):
    if not CodeSnippet.objects.exists():
        return render(request, "snippetz/no_snippets.html")

    quiz = QuizSession(request)
    quiz.create_quiz()
    return redirect("quiz:question")


def question(request):
    quiz = QuizSession(request)

    match quiz.load():
        case Ok(state):
            pass
        case Err(_):
            return redirect("quiz:start")

    if state.is_finished():
        return redirect("quiz:results")

    if request.method == "POST":
        answer_id = request.POST.get("answer_id")
        if answer_id:
            match quiz.fetch_next_snippet(state):
                case Ok(snippet):
                    state = state.record_answer(snippet.pk, int(answer_id))
                    quiz.save(state)
                case Err(_):
                    pass
            if state.is_finished():
                return redirect("quiz:results")
            return redirect("quiz:question")

    snippet = quiz.fetch_next_snippet(state).ok()
    versions = quiz.get_choices_for_snippet(state, snippet)

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


def results(request):
    quiz = QuizSession(request)

    match quiz.load():
        case Ok(state):
            pass
        case Err(_):
            return redirect("quiz:start")

    if not state.is_finished():
        return redirect("quiz:question")

    result = quiz.calculate_score(state)
    return render(request, "snippetz/results.html", result)
