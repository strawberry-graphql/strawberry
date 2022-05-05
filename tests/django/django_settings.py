SECRET_KEY = 1

INSTALLED_APPS = ["strawberry.django", "tests.django.app"]
ROOT_URLCONF = "tests.django.app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
    }
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
