import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict
from .materials import digest, encoded, material_hash, validate


def bundle(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text())
    if data.get("format") != "sentence-legacy/v1":
        raise ValueError("unsupported migration bundle")
    validate(data["pack"])
    identifiers = {i["id"] for i in data["pack"]["items"]}
    if len(identifiers) != len(data["pack"]["items"]) or identifiers != set(data["progress"]):
        raise ValueError("migration baseline/material identity mismatch")
    for identifier, progress in data["progress"].items():
        if progress["state"] not in {"New", "Learning", "Usable", "Automatic"} or any(type(progress[k]) is not int or progress[k] < 0 for k in ("uses", "sessions")):
            raise ValueError("invalid historical baseline: " + identifier)
    session_ids = set()
    for session in data["sessions"]:
        if session["session_id"] in session_ids or session["primary"] not in identifiers or not set(session["frames"]) <= identifiers or session["properties"]["Status"] != "Applied":
            raise ValueError("migration session reference/status conflict")
        session_ids.add(session["session_id"])
    for relative, expected in data["manifest"].items():
        source = path.parent / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or source.is_symlink() or not source.resolve().is_relative_to(path.parent.resolve()):
            raise ValueError("unsafe migration archive path")
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError("migration archive hash mismatch: " + relative)
    return data


def preview(db: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
    path = Path(payload["bundle"]).resolve()
    data = bundle(path)
    identity = uuid.uuid4().hex
    db.execute("INSERT INTO previews VALUES (?,?,?)", (identity, encoded({"path": str(path), "kind": "migration"}), digest(data)))
    return {"preview_id": identity, "digest": digest(data), "report": data["report"], "baseline": data["progress"], "eligible": not bool(db.execute("SELECT 1 FROM materials").fetchone())}


def accept(api: Any, db: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
    row = db.execute("SELECT * FROM previews WHERE id=?", (payload["preview_id"],)).fetchone()
    if row is None or not payload.get("confirmed"):
        raise ValueError("review migration parity before accepting")
    proposal = json.loads(row["body"])
    if proposal.get("kind") != "migration":
        raise ValueError("preview is not a migration")
    source = Path(proposal["path"])
    data = bundle(source)
    if digest(data) != row["basis"]:
        raise ValueError("migration source changed after preview")
    prior = db.execute("SELECT value FROM metadata WHERE key='migration'").fetchone()
    if prior:
        if prior[0] != digest(data):
            raise ValueError("a different baseline is already published")
        return {"migrated": True, "reused": True, "report": data["report"]}
    if db.execute("SELECT 1 FROM materials").fetchone() or db.execute("SELECT 1 FROM sessions").fetchone():
        raise ValueError("migration only publishes into a fresh learner store")
    archive = api.root / "data/imports" / ("legacy-" + digest(data)[:16])
    if archive.resolve() != source.parent:
        if archive.exists():
            if (archive / "bundle.json").read_bytes() != source.read_bytes():
                raise ValueError("migration archive destination conflict")
        else:
            shutil.copytree(source.parent, archive)
    for item in data["pack"]["items"]:
        identifier, hashed = item["id"], material_hash(item)
        db.execute("INSERT INTO materials VALUES (?,?,?,1)", (identifier, hashed, encoded(item)))
        db.execute("INSERT OR IGNORE INTO versions VALUES (?,?)", (hashed, encoded(item)))
        db.execute("INSERT INTO progress VALUES (?,?)", (identifier, encoded(data["progress"][identifier])))
        db.execute("INSERT INTO sources VALUES (?,?,?)", (data["pack"]["source"], identifier, hashed))
        db.execute("INSERT INTO legacy VALUES ('baseline',?,?)", (identifier, encoded(data["progress"][identifier])))
    for session in data["sessions"]:
        identity = session["session_id"]
        db.execute("INSERT INTO sessions VALUES (?,?,?,?)", (identity, "Applied", encoded({"id": identity, **session, "stage": "Applied"}), session["properties"].get("date:Date:start") or "unknown"))
        db.execute("INSERT INTO results VALUES (?,?,?,?,?)", (identity, encoded(session), encoded({"progress": {}}), "legacy:" + identity, digest(session)))
        db.execute("INSERT INTO legacy VALUES ('session',?,?)", (identity, encoded(session)))
    for error in data["errors"]:
        db.execute("INSERT INTO legacy VALUES ('error',?,?)", (error["id"], encoded(error)))
    db.execute("INSERT INTO legacy VALUES ('migration','report',?)", (encoded(data["report"]),))
    db.execute("INSERT INTO metadata VALUES ('migration',?)", (digest(data),))
    api._write_material_pack(data["pack"], "legacy")
    return {"migrated": True, "reused": False, "report": data["report"], "archive": str(archive)}
