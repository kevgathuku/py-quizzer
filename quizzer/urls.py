from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

from quizzer.snippetz.views import home

urlpatterns = [
    path("healthz", lambda request: HttpResponse("ok")),
    path("", home, name="home"),
    path("quiz/", include("quizzer.snippetz.urls")),
    path("admin/", admin.site.urls),
]
