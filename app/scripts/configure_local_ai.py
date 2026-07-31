import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Enable or disable the local Ollama Datasheet extractor."
    )
    parser.add_argument(
        "--enabled",
        choices=("true", "false"),
        default="true",
    )
    parser.add_argument("--model", default="qwen3-vl:4b")
    parser.add_argument("--text-model", default="qwen3:1.7b")
    parser.add_argument("--vision-model", default="qwen3-vl:2b-instruct")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434/")
    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parent.parent
    env_path = project_dir / ".env"
    if not env_path.is_file():
        raise SystemExit(f"Missing environment file: {env_path}")

    updates = {
        "AI_DATASHEET_ENABLED": str(args.enabled == "true"),
        "AI_DATASHEET_BASE_URL": args.base_url,
        "AI_DATASHEET_MODEL": args.model,
        "AI_DATASHEET_TEXT_MODEL": args.text_model,
        "AI_DATASHEET_VISION_MODEL": args.vision_model,
        "AI_DATASHEET_TIMEOUT": "1800",
        "AI_DATASHEET_CONTEXT_LENGTH": "16384",
        "AI_DATASHEET_KEEP_ALIVE": "5m",
        "AI_DATASHEET_MAX_TEXT_CHARS": "40000",
        "AI_DATASHEET_TEXT_PAGE_LIMIT": "5",
        "AI_DATASHEET_EVIDENCE_PAGE_LIMIT": "12",
        "AI_DATASHEET_HEAD_PAGES": "2",
        "AI_DATASHEET_VISION_PAGE_LIMIT": "4",
        "AI_DATASHEET_RENDER_DPI": "96",
        "AI_DATASHEET_MAX_OUTPUT_TOKENS": "3072",
        "AI_DATASHEET_RULE_SKIP_RATIO": "0.85",
        "AI_DATASHEET_WORKERS": "1",
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
    output.extend(
        f"{key}={value}" for key, value in updates.items() if key not in found
    )
    temporary = env_path.with_suffix(".env.local-ai.tmp")
    temporary.write_text("\n".join(output) + "\n", encoding="utf-8")
    temporary.replace(env_path)
    print(
        f"Local AI enabled={updates['AI_DATASHEET_ENABLED']}; "
        f"model={args.model}; base_url={args.base_url}"
    )


if __name__ == "__main__":
    main()
