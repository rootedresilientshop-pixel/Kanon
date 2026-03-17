import json
from pathlib import Path


def main():
    log_path = Path("kanon_audit.log")
    legacy_path = Path("kanon_audit.log.legacy")

    if not log_path.exists():
        log_path.write_text("", encoding="utf-8")
        return

    legacy_lines = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            legacy_lines.append(line)
            continue
        if "public_key" not in entry:
            legacy_lines.append(line)

    if legacy_lines:
        with legacy_path.open("a", encoding="utf-8") as f:
            for line in legacy_lines:
                f.write(line)
                f.write("\n")

    log_path.write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
