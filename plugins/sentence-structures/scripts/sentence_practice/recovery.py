"""Verified, additive recovery: an old checkpoint cannot erase accepted work."""
import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any, Dict


def verify(checkpoint: Path) -> Dict[str, Any]:
    checkpoint = checkpoint.resolve()
    manifest = json.loads((checkpoint / "manifest.json").read_text())
    if manifest.get("schema") != 1 or not isinstance(manifest.get("files"), dict):
        raise ValueError("unsupported checkpoint manifest")
    for relative, expected in manifest["files"].items():
        path = checkpoint / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or path.is_symlink() or not path.resolve().is_relative_to(checkpoint):
            raise ValueError("unsafe checkpoint path")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("checkpoint hash mismatch: " + relative)
    if not {"practice.sqlite3", "data/project.json"}.issubset(manifest["files"]):
        raise ValueError("checkpoint is incomplete")
    with closing(sqlite3.connect("file:" + str(checkpoint / "practice.sqlite3") + "?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or db.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("checkpoint database validation failed")
        project_id = db.execute("SELECT value FROM metadata WHERE key='project_id'").fetchone()[0]
        if project_id != json.loads((checkpoint / "data/project.json").read_text())["project_id"]:
            raise ValueError("checkpoint project identity mismatch")
        accepted = {row[0]: row[1] for row in db.execute("SELECT r.session_id,r.body FROM results r JOIN sessions s ON s.id=r.session_id WHERE s.status='Applied'")}
    return {"manifest": manifest, "project_id": project_id, "accepted": accepted}


def restore(api: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
    checkpoint = Path(payload["checkpoint"]).resolve()
    saved = verify(checkpoint)
    marker = api.root / "data/project.json"
    current = None
    if marker.exists():
        if json.loads(marker.read_text())["project_id"] != saved["project_id"]:
            raise ValueError("cannot restore a different project over this project")
        with closing(api._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            current = api._backup(db)["checkpoint"]
        live = verify(Path(current))
        for identity in live["accepted"].keys() & saved["accepted"].keys():
            if live["accepted"][identity] != saved["accepted"][identity]:
                raise ValueError("accepted identity conflict; recovery stopped")
        newer = live["accepted"].keys() - saved["accepted"].keys()
        if newer:
            # The complete verified live database is the retained continuation.
            # Overlaying it preserves all later events, repairs and projections.
            if not saved["accepted"].keys() <= live["accepted"].keys():
                raise ValueError("cannot prove a complete accepted continuation")
            saved = live
            database_source = Path(current) / "practice.sqlite3"
        else:
            # Preserve unfinished work, imports and repairs too. Explicit recovery
            # never rolls those back merely because Applied identities are equal.
            database_source = Path(current) / "practice.sqlite3"
    else:
        newer = set()
        database_source = checkpoint / "practice.sqlite3"
    staging = api.root / "data/recovery" / uuid.uuid4().hex
    staging.mkdir(parents=True)
    target_db = staging / "practice.sqlite3"
    with closing(sqlite3.connect("file:" + str(database_source) + "?mode=ro", uri=True)) as source, closing(sqlite3.connect(str(target_db))) as destination:
        source.backup(destination)
        if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("staged database validation failed")
    # Restore missing archives/material files; conflicts retain the live version.
    for relative in verify(checkpoint)["manifest"]["files"]:
        if relative in {"practice.sqlite3", "data/project.json"} or relative.startswith(("runtime/", "schemas/", "docs/")):
            continue
        target = api.root / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(checkpoint / relative, target)
    database = api.root / "data/practice.sqlite3"
    # Every public operation shares the project writer lock; no live connection
    # remains here. Keep an on-disk staged copy for interruption diagnosis.
    if database.exists():
        with closing(api._connect()) as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    os.replace(target_db, database)
    if not marker.exists():
        marker.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(checkpoint / "data/project.json", marker)
    with closing(api._connect()) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("restore readback failed")
    return {"restored": True, "preserved_sessions": sorted(newer), "before_checkpoint": current, "mode": "retain verified live continuation" if current else "standalone restore"}
