import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

import django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.utils import timezone

BACKUP_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{6}$")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_within(path, root):
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise CommandError(f"Path must stay under {root}.") from exc
    return resolved


def valid_backup(path):
    return (
        path.is_dir()
        and BACKUP_NAME.fullmatch(path.name) is not None
        and (path / "manifest.json").is_file()
        and (path / "ap_products.sqlite3").is_file()
    )


class Command(BaseCommand):
    help = "Create a consistent SQLite, media, environment, and version backup."

    def add_arguments(self, parser):
        parser.add_argument("--output", help="Backup directory name or path under BACKUP_DIR.")
        parser.add_argument("--no-prune", action="store_true", help="Skip retention cleanup.")

    def handle(self, *args, **options):
        backup_root = Path(settings.BACKUP_DIR).resolve()
        database_path = Path(settings.DATABASES["default"]["NAME"]).resolve()
        media_root = Path(settings.MEDIA_ROOT).resolve()
        runtime_root = Path(settings.RUNTIME_DATA_ROOT).resolve()
        for path in (backup_root, database_path, media_root, Path(settings.LOG_DIR), Path(settings.STATIC_ROOT)):
            ensure_within(path, runtime_root)
        backup_root.mkdir(parents=True, exist_ok=True)
        lock_path = backup_root / ".backup.lock"
        try:
            lock_descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise CommandError("Another backup is already running.") from exc

        try:
            os.write(lock_descriptor, str(os.getpid()).encode("ascii"))
            os.close(lock_descriptor)
            output = self._output_path(backup_root, options["output"])
            if output.exists():
                raise CommandError(f"Backup destination already exists: {output}")
            temporary = backup_root / f".building-{uuid.uuid4().hex}"
            temporary.mkdir()
            try:
                self._create_backup(temporary, database_path, media_root)
                temporary.replace(output)
            except Exception:
                shutil.rmtree(temporary, ignore_errors=True)
                raise
            if not options["no_prune"]:
                self._prune(backup_root, output)
            self.stdout.write(self.style.SUCCESS(f"Backup created: {output}"))
        finally:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass

    def _output_path(self, backup_root, value):
        if value:
            candidate = Path(value)
            if not candidate.is_absolute():
                candidate = backup_root / candidate
        else:
            candidate = backup_root / timezone.localtime().strftime("%Y-%m-%d_%H%M%S")
        candidate = ensure_within(candidate, backup_root)
        if not BACKUP_NAME.fullmatch(candidate.name):
            raise CommandError("Backup directory name must use YYYY-MM-DD_HHMMSS.")
        return candidate

    def _create_backup(self, destination, database_path, media_root):
        database_backup = destination / "ap_products.sqlite3"
        connections["default"].ensure_connection()
        source_connection = connections["default"].connection
        target_connection = sqlite3.connect(database_backup)
        try:
            source_connection.backup(target_connection, pages=1000)
            integrity = target_connection.execute("PRAGMA integrity_check").fetchone()[0]
            counts = {}
            for table in ("catalog_product", "catalog_productspec", "comparison_productmatch", "changes_changerequest", "audit_auditlog"):
                counts[table] = target_connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        finally:
            target_connection.close()
        if integrity != "ok":
            raise CommandError(f"SQLite integrity check failed: {integrity}")

        media_archive = destination / "media.zip"
        with zipfile.ZipFile(media_archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            if media_root.exists():
                for path in sorted(media_root.rglob("*")):
                    if path.is_file() and not path.is_symlink():
                        archive.write(path, path.relative_to(media_root).as_posix())
        with zipfile.ZipFile(media_archive) as archive:
            if archive.testzip() is not None:
                raise CommandError("Media archive verification failed.")

        environment_source = Path(settings.BASE_DIR) / ".env"
        environment_backup = destination / "environment.env"
        if not environment_source.is_file():
            raise CommandError("The application .env file is missing.")
        shutil.copy2(environment_source, environment_backup)
        try:
            environment_backup.chmod(0o600)
        except OSError:
            pass

        version_path = destination / "application_version.txt"
        git_revision = subprocess.run(
            [str(Path(settings.BASE_DIR).parent / "tools" / "Git" / "cmd" / "git.exe"), "-c", f"safe.directory={Path(settings.BASE_DIR).as_posix()}", "rev-parse", "HEAD"],
            cwd=settings.BASE_DIR,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip() or "unknown"
        version_path.write_text(
            f"git_revision={git_revision}\npython={sys.version.split()[0]}\ndjango={django.get_version()}\n",
            encoding="utf-8",
        )

        files = {}
        for path in (database_backup, media_archive, environment_backup, version_path):
            files[path.name] = {"sha256": sha256_file(path), "size": path.stat().st_size}
        manifest = {
            "format_version": 1,
            "created_at": timezone.now().isoformat(),
            "database_integrity": integrity,
            "database_counts": counts,
            "files": files,
        }
        (destination / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _prune(self, backup_root, newest):
        backups = sorted(
            [path for path in backup_root.iterdir() if valid_backup(path)],
            key=lambda path: path.name,
            reverse=True,
        )
        if not backups or backups[0] != newest:
            raise CommandError("Retention stopped because the newest backup is not valid.")
        keep = set(backups[:30])
        weekly = set()
        seen_weeks = set()
        for path in backups:
            date = datetime.strptime(path.name, "%Y-%m-%d_%H%M%S").date()
            week = date.isocalendar()[:2]
            if week not in seen_weeks and len(seen_weeks) < 12:
                seen_weeks.add(week)
                weekly.add(path)
        keep.update(weekly)
        for path in backups:
            if path in keep:
                continue
            resolved = ensure_within(path, backup_root)
            if not valid_backup(resolved):
                continue
            shutil.rmtree(resolved)
            self.stdout.write(f"Pruned old backup: {resolved.name}")
