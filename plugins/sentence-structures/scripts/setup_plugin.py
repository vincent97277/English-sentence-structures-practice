"""Register/reload this source package and enable it only in its project."""
import argparse
import json
import re
import subprocess
from pathlib import Path


PLUGIN_ID = "sentence-structures@sentence-practice-local"


def section(path, header, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = path.read_text() if path.exists() else ""
    pattern = r"(?m)^" + re.escape(header) + r"\s*\n([^\[]*)"
    match = re.search(pattern, content)
    if match:
        updated = match[1]
        for key, value in body.items():
            key_pattern = r"(?m)^" + re.escape(key) + r"\s*=.*$"
            if re.search(key_pattern, updated):
                updated = re.sub(key_pattern, key + " = " + value, updated)
            else:
                updated += key + " = " + value + "\n"
        content = content[:match.start()] + header + "\n" + updated + content[match.end():]
    else:
        content += "\n" + header + "\n" + "\n".join(key + " = " + value for key, value in body.items()) + "\n"
    path.write_text(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--codex", default="codex")
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / "plugins/sentence-structures/plugin.json").is_file():
        raise ValueError("root must contain the sentence-structures source package")
    marketplace = root / ".agents/plugins/marketplace.json"
    marketplace.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(marketplace.read_text()) if marketplace.exists() else {"name": "sentence-practice-local", "plugins": []}
    if data["name"] != "sentence-practice-local":
        raise ValueError("existing project marketplace has another identity; do not overwrite")
    data["plugins"] = [p for p in data["plugins"] if p["name"] != "sentence-structures"] + [{"name": "sentence-structures", "source": {"source": "local", "path": "./plugins/sentence-structures"}, "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": "Education & Research"}]
    marketplace.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    config = Path.home() / ".codex/config.toml"
    section(config, '[projects.' + json.dumps(str(root)) + ']', {"trust_level": '"trusted"'})
    section(root / ".codex/config.toml", '[plugins."' + PLUGIN_ID + '"]', {"enabled": "true"})
    try:
        for command in (["plugin", "marketplace", "add", str(root), "--json"], ["plugin", "add", PLUGIN_ID, "--json"]):
            subprocess.run([args.codex, *command], cwd=root, check=True)
    finally:
        section(config, '[plugins."' + PLUGIN_ID + '"]', {"enabled": "false"})


if __name__ == "__main__":
    main()
