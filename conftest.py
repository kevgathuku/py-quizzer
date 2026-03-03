import pytest

SIMPLE_STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@pytest.fixture(autouse=True)
def _use_simple_staticfiles(settings):
    settings.STORAGES = SIMPLE_STORAGES
