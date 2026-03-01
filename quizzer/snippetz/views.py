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
    state = quiz.load()

    if not state:
        return redirect("quiz:start")

    if state.is_finished():
        return redirect("quiz:results")

    if request.method == "POST":
        answer_id = request.POST.get("answer_id")
        if answer_id:
            snippet = quiz.fetch_next_snippet(state)
            if snippet:
                state = state.record_answer(snippet.pk, int(answer_id))
                quiz.save(state)
            if state.is_finished():
                return redirect("quiz:results")
            return redirect("quiz:question")

    snippet = quiz.fetch_next_snippet(state)
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
    state = quiz.load()

    if not state:
        return redirect("quiz:start")

    if not state.is_finished():
        return redirect("quiz:question")

    result = quiz.calculate_score(state)
    return render(request, "snippetz/results.html", result)
