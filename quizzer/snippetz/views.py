from django.shortcuts import redirect, render

from quizzer.snippetz.models import CodeSnippet
from quizzer.snippetz.services import QuizSession


def start_quiz(request):
    if not CodeSnippet.objects.exists():
        return render(request, "snippetz/no_snippets.html")

    quiz = QuizSession(request)
    quiz.start()
    return redirect("quiz:question")


def question(request):
    quiz = QuizSession(request)

    if not quiz._get_data():
        return redirect("quiz:start")

    if quiz.is_finished():
        return redirect("quiz:results")

    if request.method == "POST":
        version_id = request.POST.get("version_id")
        if version_id:
            snippet = quiz.get_current_snippet()
            if snippet:
                quiz.submit_answer(snippet.pk, int(version_id))
            if quiz.is_finished():
                return redirect("quiz:results")
            return redirect("quiz:question")

    snippet = quiz.get_current_snippet()
    versions = quiz.get_choices_for_snippet(snippet)
    question_ids = quiz._get_data()["question_ids"]
    answers = quiz._get_data()["answers"]
    question_number = len(answers) + 1
    total_questions = len(question_ids)

    return render(
        request,
        "snippetz/question.html",
        {
            "snippet": snippet,
            "versions": versions,
            "question_number": question_number,
            "total_questions": total_questions,
        },
    )


def results(request):
    quiz = QuizSession(request)

    if not quiz._get_data():
        return redirect("quiz:start")

    if not quiz.is_finished():
        return redirect("quiz:question")

    result = quiz.calculate_score()
    return render(request, "snippetz/results.html", result)
