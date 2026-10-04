"""One-time read-only normalization of archived Notion responses. Requires PyYAML."""
import argparse
import html
import json
import re
import shutil
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
import yaml
from sentence_practice.materials import digest, encoded, validate


def inner(path):
    raw = json.loads(path.read_text())
    return json.loads(next(c["text"] for c in raw["content"] if c["type"] == "text"))


def serial(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: serial(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serial(v) for v in value]
    return value


def effective_result(result, corrections):
    effective = deepcopy(result)
    for correction in corrections:
        for path, value in correction.get("corrected_fields", {}).items():
            parts = path.split(".")
            current = effective
            for part in parts[:-1]:
                if isinstance(current, list):
                    current = next(v for v in current if v.get("id") == part)
                else:
                    current = current.setdefault(part, {})
            current[parts[-1]] = value
    return effective


def prepare(archive, project):
    rows = {name: inner(archive / (name + "-query.json"))["results"] for name in ("structures", "errors", "sessions")}
    pages = {path.stem.replace("-", ""): inner(path) for path in (archive / "pages").glob("*.json")}
    if len(pages) != sum(map(len, rows.values())):
        raise ValueError("source page coverage mismatch")
    for name in rows:
        first = sorted(rows[name], key=lambda r: r["id"])
        second = sorted(inner(archive / (name + "-verification.json"))["results"], key=lambda r: r["id"])
        if first != second:
            raise ValueError("source rows changed during acquisition")
    items, progress, sessions = [], {}, []
    for row in sorted(rows["structures"], key=lambda r: r["Structure ID"]):
        identifier = row["Structure ID"]
        examples = [html.unescape(t.strip()) for t in re.split(r"<br\s*/?>|\n", row["Example"]) if t.strip()]
        item = {"id": identifier, "pattern": row["Pattern"], "purpose": row["Function"], "examples": examples, "priority": row["Priority"]}
        if row.get("Curriculum Notes") and row["Curriculum Notes"].strip() not in {"—", "-"}:
            item["notes"] = row["Curriculum Notes"]
        items.append(item)
        progress[identifier] = {"state": row["State"], "uses": row["Independent Uses"], "sessions": row["Independent Sessions"], "next_review": row.get("date:Next Review:start"), "last_practiced": row.get("date:Last Practiced:start"), "legacy_properties": row}
    pack = {"format": "sentence-materials/v1", "source": "Notion Structures (read-only migration 2026-10-05)", "items": items}
    validate(pack)
    for row in sorted(rows["sessions"], key=lambda r: (r.get("date:Date:start") or "", r.get("date:Applied At:start") or "", r["Session ID"])):
        page = pages[row["id"].replace("-", "")]
        text = page["text"]
        content = re.search(r"<content>\n(.*?)\n</content>", text, re.S)
        body = content[1] if content else ""
        parsed = [serial(yaml.safe_load(block)) for block in re.findall(r"```yaml\n(.*?)\n```", body, re.S)]
        results = [block["SESSION_RESULT"] for block in parsed if isinstance(block, dict) and "SESSION_RESULT" in block]
        corrections = [block["SESSION_RESULT_CORRECTION"] for block in parsed if isinstance(block, dict) and "SESSION_RESULT_CORRECTION" in block]
        plans = [block["APPLICATION_PLAN"] for block in parsed if isinstance(block, dict) and "APPLICATION_PLAN" in block]
        if not results and "## SESSION_RESULT v1" in body:
            listed = body.split("## SESSION_RESULT v1", 1)[1]
            mapped = "\n".join(line[2:] for line in listed.strip().splitlines() if line.startswith("- "))
            results = [serial(yaml.safe_load(mapped))]
        result = results[0] if results else {}
        effective = effective_result(result, corrections)
        frames = effective.get("practiced", [])
        if not frames:
            frames = [{"id": row["Primary Structure"], **effective}]
        primary = row["Primary Structure"]
        identifiers = [f["id"] for f in frames]
        if primary not in progress or any(i not in progress for i in identifiers):
            raise ValueError("dangling historical reference")
        sessions.append({"session_id": row["Session ID"], "primary": primary, "purpose": row.get("Session Purpose") or effective.get("session_purpose", "unknown"), "policy": effective.get("policy_revision", "legacy-v1" if effective.get("schema_version") == 1 else "legacy-partial"), "synthetic": row["Synthetic"] == "__YES__", "properties": row, "original_result": result, "corrections": corrections, "plans": plans, "effective_legacy_result": effective, "frames": {i: {"first": "unknown", "first_full": "unknown", "productions": []} for i in identifiers}, "practice_time": "unknown", "body": body})
    warnings = ["All 13 sessions lack reliable actual practice-ended timestamps; no delayed credit manufactured.", "No full original ChatGPT transcript is available; summaries are not verbatim conversation.", "Notion acquisition is not a cross-source atomic snapshot; row queries were repeated and matched.", "S005 baseline Usable/9 uses/3 sessions retained; secondary-based possible 10/4 discrepancy not replayed.", "Legacy resolved Error has one occurrence and an empty body; missing ledger is unknown.", "Group/Level/Review editorial metadata retained in raw properties; no auto-merge."]
    for name in ("sentence-structures-requirements.md", "sentence-structures-implementation-spec.md"):
        target = archive / "original-documents" / name
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(project / name, target)
    import hashlib
    files = {str(path.relative_to(archive)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(archive.rglob("*")) if path.is_file() and path.name not in {"bundle.json", "parity-report.json"}}
    report = {"materials": len(items), "sessions": len(sessions), "errors": len(rows["errors"]), "corrections": sum(len(s["corrections"]) for s in sessions), "plans": sum(len(s["plans"]) for s in sessions), "versions": {v: sum(s["policy"] == v for s in sessions) for v in {s["policy"] for s in sessions}}, "source_pages": len(pages), "warnings": warnings, "s005": progress["S005"]}
    bundle = {"format": "sentence-legacy/v1", "pack": pack, "progress": progress, "sessions": sessions, "errors": rows["errors"], "manifest": files, "report": report}
    (archive / "bundle.json").write_text(encoded(bundle) + "\n")
    (archive / "parity-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return {"bundle": str(archive / "bundle.json"), "digest": digest(bundle), **{k:v for k,v in report.items() if k not in {"s005", "warnings"}}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.archive.resolve(), args.project.resolve()), ensure_ascii=False))
