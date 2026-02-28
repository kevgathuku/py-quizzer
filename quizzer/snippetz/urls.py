from django.urls import path

from quizzer.snippetz import views

app_name = "quiz"

urlpatterns = [
    path("start/", views.start_quiz, name="start"),
    path("question/", views.question, name="question"),
    path("results/", views.results, name="results"),
]
