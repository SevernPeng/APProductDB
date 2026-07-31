import argparse
import ipaddress
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Configure APProductDB D-drive runtime paths.")
    parser.add_argument("--host", required=True, help="Private LAN IPv4 address.")
    parser.add_argument("--data-root", default=r"D:\APProductDB")
    args = parser.parse_args()

    host = ipaddress.ip_address(args.host)
    if host.version != 4 or not host.is_private:
        raise SystemExit("--host must be a private IPv4 address.")
    data_root = Path(args.data_root).resolve()
    if os.name == "nt" and data_root.drive.upper() != "D:":
        raise SystemExit("All APProductDB runtime data must remain on D:.")

    project_dir = Path(__file__).resolve().parent.parent
    env_path = project_dir / ".env"
    if not env_path.is_file():
        raise SystemExit(f"Missing environment file: {env_path}")
    updates = {
        "DJANGO_DEBUG": "False",
        "DJANGO_ALLOWED_HOSTS": f"127.0.0.1,localhost,{host}",
        "DJANGO_CSRF_TRUSTED_ORIGINS": f"http://{host}:8000",
        "AP_PRODUCT_DATA_ROOT": str(data_root),
        "AP_PRODUCT_REQUIRE_D_DRIVE": "True",
        "DATABASE_PATH": str(data_root / "data" / "ap_products.sqlite3"),
        "MEDIA_ROOT": str(data_root / "media"),
        "STATIC_ROOT": str(data_root / "staticfiles"),
        "LOG_DIR": str(data_root / "logs"),
        "BACKUP_DIR": str(data_root / "backups"),
    }
    lines = env_path.read_text(encoding="utf-8").splitlines()
    found = set()
    output = []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                output.append(f"{key}={updates[key]}")
                found.add(key)
                continue
        output.append(line)
    for key, value in updates.items():
        if key not in found:
            output.append(f"{key}={value}")
    temporary = env_path.with_suffix(".env.tmp")
    temporary.write_text("\n".join(output) + "\n", encoding="utf-8")
    temporary.replace(env_path)
    for directory in ("data", "media", "staticfiles", "logs", "backups", "restore-tests"):
        (data_root / directory).mkdir(parents=True, exist_ok=True)
    print(f"Configured runtime host {host}; all data paths are under {data_root}.")


if __name__ == "__main__":
    main()
