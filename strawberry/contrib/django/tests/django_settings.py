SECRET_KEY = 1

INSTALLED_APPS = ["strawberry.contrib.django", "strawberry.contrib.django.tests"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
    }
]

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "tests/django.sqlite"}
}
