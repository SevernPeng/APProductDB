import json
import shutil
import sqlite3
import uuid
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from .backup_database import ensure_within, sha256_file, valid_backup


class Command(BaseCommand):
    help = "Restore a backup into an isolated D-drive directory and verify it."

    def add_arguments(self, parser):
        parser.add_argument("--backup", default="latest", help="Backup path/name or latest.")
        parser.add_argument("--keep-restored", action="store_true")

    def handle(self, *args, **options):
        backup_root = Path(settings.BACKUP_DIR).resolve()
        backup = self._select_backup(backup_root, options["backup"])
        restore_root = Path(settings.RUNTIME_DATA_ROOT).resolve() / "restore-tests"
        restore_root.mkdir(parents=True, exist_ok=True)
        workspace = restore_root / f"restore-{uuid.uuid4().hex}"
        workspace.mkdir()
        try:
            report = self._verify_and_restore(backup, workspace)
            reports = restore_root / "reports"
            reports.mkdir(exist_ok=True)
            report_path = reports / f"{timezone.localtime().strftime('%Y-%m-%d_%H%M%S')}.json"
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Restore test passed: {report_path}"))
        finally:
            if not options["keep_restored"]:
                shutil.rmtree(workspace, ignore_errors=True)

    def _select_backup(self, backup_root, value):
        if value == "latest":
            backups = sorted(
                [path for path in backup_root.iterdir() if valid_backup(path)],
                key=lambda path: path.name,
                reverse=True,
            )
            if not backups:
                raise CommandError("No valid backup is available.")
            return backups[0]
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = backup_root / candidate
        candidate = ensure_within(candidate, backup_root)
        if not valid_backup(candidate):
            raise CommandError("The selected backup is incomplete or invalid.")
        return candidate

    def _verify_and_restore(self, backup, workspace):
        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        for name, metadata in manifest["files"].items():
            path = backup / name
            if not path.is_file() or sha256_file(path) != metadata["sha256"]:
                raise CommandError(f"Backup checksum mismatch: {name}")

        database = workspace / "ap_products.sqlite3"
        shutil.copy2(backup / "ap_products.sqlite3", database)
        connection = sqlite3.connect(database)
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            required = {"django_migrations", "catalog_product", "catalog_productspec", "comparison_productmatch", "changes_changerequest", "audit_auditlog"}
            missing = sorted(required - tables)
            if integrity != "ok" or missing:
                raise CommandError(f"Restored database failed validation; integrity={integrity}, missing={missing}")
            counts = {
                table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in sorted(required - {"django_migrations"})
            }
        finally:
            connection.close()

        media_target = workspace / "media"
        media_target.mkdir()
        media_count = 0
        with zipfile.ZipFile(backup / "media.zip") as archive:
            for member in archive.infolist():
                target = (media_target / member.filename).resolve()
                ensure_within(target, media_target)
                archive.extract(member, media_target)
                if not member.is_dir():
                    media_count += 1
        return {
            "tested_at": timezone.now().isoformat(),
            "backup": backup.name,
            "database_integrity": integrity,
            "database_counts": counts,
            "media_files": media_count,
            "status": "passed",
        }
