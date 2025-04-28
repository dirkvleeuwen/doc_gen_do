import os
import sys
from pathlib import Path
from django.urls import reverse_lazy
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------------------
# SECURITY & DEBUG
# ------------------------------------------------------------------------------
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY ontbreekt in je environment")

debug_env = os.environ.get("DEBUG")
if debug_env is None:
    raise ImproperlyConfigured("DEBUG ontbreekt in je environment")
DEBUG = debug_env.lower() in ("1", "true", "yes")

hosts = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in hosts.split(",") if h.strip()] or ["*"]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS ontbreekt in je environment")

# SECRET_KEY = os.getenv("SECRET_KEY")
# if not SECRET_KEY and os.getenv("DJANGO_ENV") == "production":
#     raise ValueError("No SECRET_KEY set for production environment!")

# DEBUG = os.getenv("DEBUG", "False") == "True"
# ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "")
# ALLOWED_HOSTS = [h.strip() for h in allowed_hosts.split(",") if h.strip()]
# if DEBUG and not ALLOWED_HOSTS:
#     ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

CSRF_TRUSTED_ORIGINS = [
    "https://jouwdomein.nl",
    "https://www.jouwdomein.nl",
]

# ------------------------------------------------------------------------------
# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        # "USER": "user9843yy34hi",
        # "PASSWORD": "pRWahYuR!qAXza*xqhrA&e47*mdur1RGEGSmsTqwktK#V!5vcadEmfCXG!pR%JhH",
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {"sslmode": "require"},
    }
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.environ["DB_NAME"],
#         "USER": os.environ["DB_USER"],
#         "PASSWORD": os.environ["DB_PASSWORD"],
#         "HOST": os.environ["DB_HOST"],
#         "PORT": os.environ["DB_PORT", "5432"],
#         # eventueel TEST overrides
#         "TEST": {"MIRROR": None},
#     }
# }

# # Tijdens pytest draaien: overschrijf naar in-memory sqlite
# if any("pytest" in arg for arg in sys.argv):
#     DATABASES["default"] = {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": ":memory:",
#     }

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
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
# STORAGES = {
#     "staticfiles": {
#         "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
#         "OPTIONS": {
#             "bucket_name": os.getenv("AWS_STORAGE_BUCKET_NAME"),
#             "region_name": os.getenv("AWS_S3_REGION_NAME", "eu-central-1"),
#             "location": "static",
#             "object_parameters": {"CacheControl": "max-age=86400"},
#             "file_overwrite": True,
#             "querystring_auth": False,
#             "custom_domain": (
#                 f"{os.getenv('AWS_STORAGE_BUCKET_NAME')}"
#                 f".s3.{os.getenv('AWS_S3_REGION_NAME','eu-central-1')}.amazonaws.com"
#             ),
#         },
#     },
# }
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles_collected"

# ----------------------------------------------------------------------------
# EMAIL
# ----------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
DEFAULT_FROM_EMAIL = os.environ["EMAIL_HOST_USER"]

# ----------------------------------------------------------------------------
# OTHER SETTINGS
# ----------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

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

# ----------------------------------------------------------------------------
# TEMPLATES
# ----------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Voeg hier je eigen template-mappen toe, als je die hebt
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # de standaard context processors
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]