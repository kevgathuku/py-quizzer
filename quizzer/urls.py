from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", lambda request: redirect("quiz:start")),
    path("quiz/", include("quizzer.snippetz.urls")),
    path("admin/", admin.site.urls),
]
