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

CSRF_TRUSTED_ORIGINS = [
    "https://jouwdomein.nl",
    "https://www.jouwdomein.nl",
]

# ------------------------------------------------------------------------------
# FEATURE FLAGS
# ------------------------------------------------------------------------------
# Met de env-variabele ENABLE_APPROVALS kun je de approvals app aan- of uitzetten
# Uitzetten met `ENABLE_APPROVALS=0` of `false`, aanzetten met `ENABLE_APPROVALS=1` of `true`
ENABLE_APPROVALS = os.environ.get("ENABLE_APPROVALS", "true").lower() in ("1", "true", "yes")

# ------------------------------------------------------------------------------
# DATABASES
# ------------------------------------------------------------------------------
# Met de env‑variabele USE_SQLITE kun je lokaal wisselen tussen SQLite en
# dezelfde PostgreSQL‑database als in productie.
# Wisselen door de env‑variabele `USE_SQLITE` in te stellen op `1` of `true`.
# Altijd in de terminal uitvoeren waarin ook de Django‑server draait.
# Dit is handig voor lokale ontwikkeling zonder dat je een PostgreSQL‑database
# hoeft te draaien.
# Uitzetten met `USE_SQLITE=0` of `false`.
SQLITE_SWITCH = os.getenv("USE_SQLITE", "false").lower() in ("1", "true", "yes")

if DEBUG and SQLITE_SWITCH:
    # Gebruik een eenvoudige SQLite‑database wanneer DEBUG=True en
    # USE_SQLITE geactiveerd is (bijv. `export USE_SQLITE=1`)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # Val terug op PostgreSQL (productie of development)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["DB_NAME"],
            "USER": os.environ["DB_USER"],
            "PASSWORD": os.environ["DB_PASSWORD"],
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "OPTIONS": {"sslmode": "require"},
        }
    }

# ------------------------------------------------------------------------------
# APPLICATIONS & MIDDLEWARE
# ------------------------------------------------------------------------------
# Basisapplicaties die altijd geladen worden
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

# Voeg approvals app alleen toe als deze is ingeschakeld
if ENABLE_APPROVALS:
    INSTALLED_APPS.append("approvals.apps.ApprovalsConfig")

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
# STATIC
# -------------------------------------------------------------------------------
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

if not DEBUG:
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
                'instrument_generator.context_processors.sqlite_mode',
                'instrument_generator.context_processors.approvals_enabled',
            ],
        },
    },
]

# Development overrides for local testing
if DEBUG:
    # Disable SSL redirect and secure cookies in development
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

    # Disable HSTS so browser geen HTTPS afdwingt
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

    # Use console email backend to avoid SMTP requirement
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    ADMINS = [
        ("Site Admin", "admin@doc-gen.eu"),
    ]