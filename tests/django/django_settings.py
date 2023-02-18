SECRET_KEY = 1

INSTALLED_APPS = ["tests.django.app"]
ROOT_URLCONF = "tests.django.app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
    }
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

# This is for channels integration, but only one django settings can be used
# per pytest_django settings
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
