import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

from config.env import env_bool, env_int, env_list

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")
RUNTIME_DATA_ROOT = Path(os.getenv("AP_PRODUCT_DATA_ROOT", PROJECT_ROOT)).resolve()
RUNTIME_ROOT = Path(
    os.getenv("AP_PRODUCT_RUNTIME_ROOT", RUNTIME_DATA_ROOT / "runtime")
).resolve()
IS_TESTING = "test" in sys.argv or any("pytest" in arg.lower() for arg in sys.argv)


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in .env or the environment.")

DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")
if IS_TESTING and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "catalog.apps.CatalogConfig",
    "comparison.apps.ComparisonConfig",
    "changes.apps.ChangesConfig",
    "audit.apps.AuditConfig",
    "imports.apps.ImportsConfig",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if not IS_TESTING:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.role_capabilities",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(os.getenv("DATABASE_PATH", PROJECT_ROOT / "data" / "ap_products.sqlite3")),
        "OPTIONS": {"timeout": 20},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = ["accounts.backends.CompanyEmailBackend"]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "America/Mexico_City")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = Path(os.getenv("STATIC_ROOT", RUNTIME_ROOT / "staticfiles"))
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if IS_TESTING
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", PROJECT_ROOT / "media"))
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", RUNTIME_ROOT / "backups"))
LOG_DIR = Path(os.getenv("LOG_DIR", RUNTIME_ROOT / "logs"))
RESTORE_TEST_DIR = Path(os.getenv("RESTORE_TEST_DIR", RUNTIME_ROOT / "restore-tests"))
REQUIRE_D_DRIVE = env_bool("AP_PRODUCT_REQUIRE_D_DRIVE", False)
if REQUIRE_D_DRIVE and os.name == "nt" and not IS_TESTING and RUNTIME_DATA_ROOT.drive.upper() != "D:":
    raise ImproperlyConfigured("AP_PRODUCT_DATA_ROOT must be located on the D: drive.")
for data_name, data_path in {
    "database": DATABASES["default"]["NAME"],
    "media": MEDIA_ROOT,
}.items():
    try:
        Path(data_path).resolve().relative_to(RUNTIME_DATA_ROOT)
    except ValueError as exc:
        raise ImproperlyConfigured(
            f"The {data_name} path must stay under {RUNTIME_DATA_ROOT}."
        ) from exc
try:
    RUNTIME_ROOT.relative_to(RUNTIME_DATA_ROOT)
except ValueError as exc:
    raise ImproperlyConfigured(
        f"AP_PRODUCT_RUNTIME_ROOT must stay under {RUNTIME_DATA_ROOT}."
    ) from exc
for runtime_name, runtime_path in {
    "static": STATIC_ROOT,
    "logs": LOG_DIR,
    "backups": BACKUP_DIR,
    "restore tests": RESTORE_TEST_DIR,
}.items():
    try:
        Path(runtime_path).resolve().relative_to(RUNTIME_ROOT)
    except ValueError as exc:
        raise ImproperlyConfigured(
            f"The {runtime_name} path must stay under {RUNTIME_ROOT}."
        ) from exc
if not IS_TESTING:
    for runtime_directory in {
        DATABASES["default"]["NAME"].parent,
        MEDIA_ROOT,
        STATIC_ROOT,
        LOG_DIR,
        BACKUP_DIR,
        RESTORE_TEST_DIR,
    }:
        runtime_directory.mkdir(parents=True, exist_ok=True)

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", SECURE_SSL_REDIRECT)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", SECURE_SSL_REDIRECT)
SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", 0, minimum=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        }
    },
    "handlers": {
        "application_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "application.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "standard",
            "level": "INFO",
            "encoding": "utf-8",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "error.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "standard",
            "level": "ERROR",
            "encoding": "utf-8",
        },
        "waitress_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "waitress.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "standard",
            "level": "INFO",
            "encoding": "utf-8",
        },
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console", "application_file"], "level": "INFO"},
    "loggers": {
        "django.request": {
            "handlers": ["console", "error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "waitress": {
            "handlers": ["console", "waitress_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

if IS_TESTING:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {"null": {"class": "logging.NullHandler"}},
        "root": {"handlers": ["null"], "level": "WARNING"},
    }
