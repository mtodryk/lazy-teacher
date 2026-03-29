from settings.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable throttling in tests
REST_FRAMEWORK = {  # type: ignore[assignment]
    **REST_FRAMEWORK,  # type: ignore[name-defined]
    "DEFAULT_THROTTLE_RATES": {
        "expensive_operation": "1000/min",
    },
}
