#!/usr/bin/env python3
"""The single public JSON operation boundary used by the practice skill."""
import argparse
import json
import sys
from pathlib import Path
from sentence_practice import Practice
from sentence_practice.materials import load_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    args = parser.parse_args()
    try:
        request = load_json(args.request.read_text(encoding="utf-8"))
        if not isinstance(request, dict) or not isinstance(request.get("operation"), str):
            raise ValueError("request requires an operation")
        marker = args.root.resolve() / "data/project.json"
        if request["operation"] not in {"initialize", "restore"}:
            if not marker.is_file() or request.get("project_id") != load_json(marker.read_text())["project_id"]:
                raise ValueError("request must name the selected project's identity")
        result = Practice(args.root).execute(request)
        print(json.dumps({"status": "ok", "result": result}, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as error:
        print(json.dumps({"status": "conflict" if "conflict" in str(error) or "stale" in str(error) else "failed", "error": str(error), "stop_questions": True}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
