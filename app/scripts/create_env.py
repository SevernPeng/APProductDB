import secrets
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent
ENV_PATH = APP_DIR / ".env"


def main():
    if ENV_PATH.exists():
        print(f"Environment file already exists: {ENV_PATH}")
        return
    secret = secrets.token_urlsafe(64)
    runtime_root = PROJECT_ROOT / "runtime"
    values = [
        f"DJANGO_SECRET_KEY={secret}",
        "DJANGO_DEBUG=False",
        "DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost",
        "DJANGO_CSRF_TRUSTED_ORIGINS=",
        "DJANGO_TIME_ZONE=America/Mexico_City",
        "AP_PRODUCT_REQUIRE_D_DRIVE=False",
        f"AP_PRODUCT_DATA_ROOT={PROJECT_ROOT}",
        f"AP_PRODUCT_RUNTIME_ROOT={runtime_root}",
        f"DATABASE_PATH={PROJECT_ROOT / 'data' / 'ap_products.sqlite3'}",
        f"MEDIA_ROOT={PROJECT_ROOT / 'media'}",
        f"STATIC_ROOT={runtime_root / 'staticfiles'}",
        f"LOG_DIR={runtime_root / 'logs'}",
        f"BACKUP_DIR={runtime_root / 'backups'}",
        f"RESTORE_TEST_DIR={runtime_root / 'restore-tests'}",
    ]
    ENV_PATH.write_text("\n".join(str(value) for value in values) + "\n", encoding="utf-8")
    print(f"Created environment file: {ENV_PATH}")


if __name__ == "__main__":
    main()
