import os
import sys
from pathlib import Path
from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------------------
# SECURITY & DEBUG
# ------------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY and os.getenv("DJANGO_ENV") == "production":
    raise ValueError("No SECRET_KEY set for production environment!")

DEBUG = os.getenv("DEBUG", "False") == "True"
allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts.split(",") if h.strip()]
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

CSRF_TRUSTED_ORIGINS = [
    "https://doc-gen.eu",
    "https://www.doc-gen.eu",
    "https://35.156.89.125",
]

# ------------------------------------------------------------------------------
# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
        # eventueel TEST overrides
        "TEST": {"MIRROR": None},
    }
}

# Tijdens pytest draaien: overschrijf naar in-memory sqlite
if any("pytest" in arg for arg in sys.argv):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }

# ------------------------------------------------------------------------------
# APPLICATIONS & MIDDLEWARE
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Your apps
    "instruments",
    "accounts",
    "mailer",
    "widget_tweaks",
    # Third‑party
    "storages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = "instrument_generator.urls"
WSGI_APPLICATION = "instrument_generator.wsgi.application"

# ----------------------------------------------------------------------------
# AUTHENTICATION
# ----------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.CustomUser"
AUTHENTICATION_BACKENDS = ["accounts.auth_backends.ApprovedUserBackend"]
LOGIN_URL = reverse_lazy("accounts:login")
LOGIN_REDIRECT_URL = "/instruments/submissions/"
LOGOUT_REDIRECT_URL = "/instruments/submissions/"

# -------------------------------------------------------------------------------
# STORAGES (Django ≥4.2 API) – Static files on S3
# -------------------------------------------------------------------------------
STORAGES = {
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": os.getenv("AWS_STORAGE_BUCKET_NAME"),
            "region_name": os.getenv("AWS_S3_REGION_NAME", "eu-central-1"),
            "location": "static",
            "object_parameters": {"CacheControl": "max-age=86400"},
            "file_overwrite": True,
            "querystring_auth": False,
            "custom_domain": (
                f"{os.getenv('AWS_STORAGE_BUCKET_NAME')}"
                f".s3.{os.getenv('AWS_S3_REGION_NAME','eu-central-1')}.amazonaws.com"
            ),
        },
    },
}
STATIC_URL = f"https://{STORAGES['staticfiles']['OPTIONS']['custom_domain']}/static/"
STATIC_ROOT = BASE_DIR / "staticfiles_collected"

# ----------------------------------------------------------------------------
# EMAIL
# ----------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mail.privateemail.com"
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_HOST_USER")

# ----------------------------------------------------------------------------
# OTHER SETTINGS
# ----------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# PATH voor pdflatex
os.environ["PATH"] += os.pathsep + "/usr/bin/pdflatex"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        }
    },
}
