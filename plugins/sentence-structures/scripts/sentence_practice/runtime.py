import json
import os
import sqlite3
import uuid
import hashlib
import shutil
import fcntl
from copy import deepcopy
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .materials import digest, encoded, material_hash, validate
from .policy import POLICY, elapsed, frame, local_day, project
from .selection import select
from .recovery import restore, verify
from . import repair, migration


class PracticeError(ValueError):
    pass


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x") as output:
            output.write(encoded(value) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp, path)
        directory = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temp.exists():
            temp.unlink()


class Practice:
    def __init__(self, root: Path, clock: Optional[Callable[[], str]] = None):
        self.root = Path(root).resolve()
        if self.root.is_relative_to(Path(__file__).resolve().parents[2]):
            raise PracticeError("learner data cannot live in the plugin package/cache")
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())

    def _connect(self) -> sqlite3.Connection:
        if not (self.root / "data/project.json").is_file():
            raise PracticeError("project is not initialized")
        database = self.root / "data/practice.sqlite3"
        if not database.is_file():
            raise PracticeError("project database missing; restore a verified export")
        db = sqlite3.connect(str(database), timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        marker = json.loads((self.root / "data/project.json").read_text())
        try:
            identity = db.execute("SELECT value FROM metadata WHERE key='project_id'").fetchone()[0]
            if identity != marker["project_id"]:
                raise PracticeError("project marker/database identity mismatch")
        except Exception:
            db.close()
            raise
        return db

    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if request.get("operation") in {"initialize", "restore"}:
            (self.root / "data").mkdir(parents=True, exist_ok=True)
        if not (self.root / "data").is_dir():
            raise PracticeError("project not initialized")
        with (self.root / "data/.writer-lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            marker = self.root / "data/project.json"
            if request.get("project_id") and marker.exists() and request["project_id"] != json.loads(marker.read_text())["project_id"]:
                raise PracticeError("wrong project identity")
            return self._execute(request)

    def _execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        operation = request["operation"]
        payload = request.get("payload", {})
        if operation == "initialize":
            return self._initialize(payload)
        if operation == "restore":
            try:
                return restore(self, payload)
            except (ValueError, OSError, sqlite3.Error) as error:
                raise PracticeError(str(error)) from error
        if operation == "finish":
            return self._finish(request)
        request_hash = digest({"operation": operation, "payload": payload})
        with closing(self._connect()) as db, db:
            if operation in {"progress", "resume", "history", "diagnostics", "select"}:
                return self._dispatch(db, operation, payload)
            db.execute("BEGIN IMMEDIATE")
            identity = request.get("operation_id")
            if not isinstance(identity, str) or not identity:
                raise PracticeError("operation_id is required")
            prior = db.execute("SELECT * FROM operations WHERE id=?", (identity,)).fetchone()
            if prior:
                if prior["hash"] != request_hash:
                    raise PracticeError("operation identity conflict")
                return json.loads(prior["result"])
            result = self._dispatch(db, operation, payload)
            db.execute("INSERT INTO operations VALUES (?,?,?)", (identity, request_hash, encoded(result)))
            return result

    def _initialize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        marker = self.root / "data/project.json"
        database = self.root / "data/practice.sqlite3"
        if marker.exists():
            with closing(self._connect()) as existing:
                if existing.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise PracticeError("database integrity check failed")
            return {"initialized": True, **json.loads(marker.read_text())}
        if database.exists():
            raise PracticeError("unmarked database exists; recover before initialization")
        project_id = uuid.uuid4().hex
        temporary = database.with_suffix(".initializing")
        if temporary.exists():
            temporary.unlink()
        with closing(sqlite3.connect(str(temporary))) as db, db:
            db.executescript("""
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT);
                CREATE TABLE imports(preview_id TEXT PRIMARY KEY, response TEXT);
                CREATE TABLE sources(source TEXT, material_id TEXT, hash TEXT, PRIMARY KEY(source,material_id,hash));
                CREATE TABLE rule_activity(key TEXT PRIMARY KEY, at TEXT);
                CREATE TABLE materials(id TEXT PRIMARY KEY, hash TEXT NOT NULL, body TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE versions(hash TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE progress(id TEXT PRIMARY KEY REFERENCES materials(id), body TEXT NOT NULL);
                CREATE TABLE sessions(id TEXT PRIMARY KEY, status TEXT NOT NULL, body TEXT NOT NULL, created TEXT NOT NULL);
                CREATE UNIQUE INDEX one_unfinished ON sessions((1)) WHERE status!='Applied';
                CREATE TABLE previews(id TEXT PRIMARY KEY, body TEXT NOT NULL, basis TEXT NOT NULL);
                CREATE TABLE operations(id TEXT PRIMARY KEY, hash TEXT NOT NULL, result TEXT NOT NULL);
                CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT REFERENCES sessions(id), kind TEXT, body TEXT, at TEXT);
                CREATE TABLE results(session_id TEXT PRIMARY KEY REFERENCES sessions(id), body TEXT NOT NULL, plan TEXT NOT NULL, operation_id TEXT NOT NULL, request_hash TEXT NOT NULL);
                CREATE TABLE activity(id TEXT PRIMARY KEY REFERENCES materials(id), at TEXT, kind TEXT);
                CREATE TABLE weaknesses(key TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE legacy(kind TEXT, id TEXT, body TEXT NOT NULL, PRIMARY KEY(kind,id));
                CREATE TABLE repairs(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            """)
            db.execute("INSERT INTO metadata VALUES ('project_id',?)", (project_id,))
            db.executescript("""
                CREATE TRIGGER immutable_events_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'events are immutable'); END;
                CREATE TRIGGER immutable_events_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'events are immutable'); END;
                CREATE TRIGGER immutable_results_update BEFORE UPDATE ON results BEGIN SELECT RAISE(ABORT,'results are immutable'); END;
                CREATE TRIGGER immutable_results_delete BEFORE DELETE ON results BEGIN SELECT RAISE(ABORT,'results are immutable'); END;
            """)
        os.replace(temporary, database)
        atomic_json(marker, {"project_id": project_id, "timezone": "Asia/Taipei", "schema": 1, "test_mode": bool(payload.get("test_mode"))})
        return {"initialized": True, **json.loads(marker.read_text())}

    def _write_material_pack(self, pack: Dict[str, Any], name: str) -> None:
        atomic_json(self.root / "materials" / (name + ".json"), pack)

    def _dispatch(self, db: sqlite3.Connection, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if operation in {"preview_materials", "accept_materials", "accept_migration", "apply_repair"} and db.execute("SELECT 1 FROM sessions WHERE status='Finalizing'").fetchone():
            raise PracticeError("complete frozen finalization before another write")
        if operation == "preview_materials":
            validate(payload["pack"])
            identity = uuid.uuid4().hex
            basis = digest([dict(row) for row in db.execute("SELECT * FROM materials ORDER BY id")])
            retire = payload.get("retire", [])
            if not isinstance(retire, list) or any(not db.execute("SELECT 1 FROM materials WHERE id=?", (i,)).fetchone() for i in retire):
                raise PracticeError("retirement requires known IDs")
            differences = []
            for entry in payload["pack"]["items"]:
                item = {"priority": "High", **entry}
                old = db.execute("SELECT * FROM materials WHERE id=?", (item.get("id"),)).fetchone() if item.get("id") else db.execute("SELECT * FROM materials WHERE hash=?", (material_hash(item),)).fetchone()
                kind = "reuse" if old and old["hash"] == material_hash(item) else ("revision" if old else ("conflict" if item.get("id") else "addition"))
                differences.append({"kind": kind, "id": old["id"] if old else item.get("id"), "before": json.loads(old["body"]) if old else None, "after": item, "similar": [row["id"] for row in db.execute("SELECT id,body FROM materials") if json.loads(row["body"])["pattern"] == item["pattern"] and (not old or row["id"] != old["id"])]})
            db.execute("INSERT INTO previews VALUES (?,?,?)", (identity, encoded({"pack": payload["pack"], "retire": retire}), basis))
            return {"preview_id": identity, "count": len(payload["pack"]["items"]), "differences": differences, "retire": retire, "default_priority": "High"}
        if operation == "accept_materials":
            prior = db.execute("SELECT response FROM imports WHERE preview_id=?", (payload["preview_id"],)).fetchone()
            if prior:
                return json.loads(prior[0])
            preview = db.execute("SELECT * FROM previews WHERE id=?", (payload["preview_id"],)).fetchone()
            if not preview:
                raise PracticeError("unknown preview")
            basis = digest([dict(row) for row in db.execute("SELECT * FROM materials ORDER BY id")])
            if basis != preview["basis"]:
                raise PracticeError("material preview is stale")
            envelope = json.loads(preview["body"])
            pack = envelope["pack"]
            ids = []
            for entry in pack["items"]:
                item = dict(entry)
                item.setdefault("priority", "High")
                hash_value = material_hash(item)
                existing = db.execute("SELECT * FROM materials WHERE hash=?", (hash_value,)).fetchone()
                if existing and "id" not in item:
                    item["id"] = existing["id"]
                elif "id" not in item:
                    numbers = [int(row[0][1:]) for row in db.execute("SELECT id FROM materials")]
                    item["id"] = "S%03d" % (max(numbers, default=0) + 1)
                elif not db.execute("SELECT 1 FROM materials WHERE id=?", (item["id"],)).fetchone():
                    raise PracticeError("unknown local ID; new source must omit id")
                old = db.execute("SELECT hash FROM materials WHERE id=?", (item["id"],)).fetchone()
                if old and old["hash"] != hash_value and not payload.get("allow_revision"):
                    raise PracticeError("revision requires acceptance of its differences")
                db.execute("INSERT OR IGNORE INTO versions VALUES (?,?)", (hash_value, encoded(item)))
                db.execute("INSERT INTO materials(id,hash,body) VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET hash=excluded.hash,body=excluded.body", (item["id"], hash_value, encoded(item)))
                db.execute("INSERT OR IGNORE INTO sources VALUES (?,?,?)", (pack["source"], item["id"], hash_value))
                db.execute("INSERT OR IGNORE INTO progress VALUES (?,?)", (item["id"], encoded({"state": "New", "uses": 0, "sessions": 0, "next_review": None})))
                ids.append(item["id"])
            atomic_json(self.root / "materials" / (digest(pack) + ".json"), {**pack, "items": [json.loads(db.execute("SELECT body FROM materials WHERE id=?", (identifier,)).fetchone()[0]) for identifier in ids]})
            for identifier in envelope["retire"]:
                db.execute("UPDATE materials SET active=0 WHERE id=?", (identifier,))
            response = {"ids": ids, "retired": envelope["retire"], "pack": {**pack, "items": [json.loads(db.execute("SELECT body FROM materials WHERE id=?", (i,)).fetchone()[0]) for i in ids]}}
            db.execute("INSERT INTO imports VALUES (?,?)", (payload["preview_id"], encoded(response)))
            return response
        if operation == "progress":
            return {"materials": [{**json.loads(row["material"]), **json.loads(row["progress"]), "active": bool(row["active"])} for row in db.execute("SELECT m.body material,p.body progress,m.active FROM materials m JOIN progress p ON p.id=m.id ORDER BY m.id")]}
        if operation in {"start", "select"}:
            active = db.execute("SELECT * FROM sessions WHERE status!='Applied'").fetchone()
            if active and operation == "start":
                if payload.get("new_session"):
                    raise PracticeError("finalize the existing session before requesting a new one")
                return {**json.loads(active["body"]), "status": active["status"]}
            marker = json.loads((self.root / "data/project.json").read_text())
            materials = [{**json.loads(row["body"]), **json.loads(row["progress"]), "active": bool(row["active"])} for row in db.execute("SELECT m.*,p.body progress FROM materials m JOIN progress p ON p.id=m.id")]
            history = [r for r in self._accepted(db) if marker["test_mode"] or not r.get("synthetic")]
            weaknesses = {row["key"]: json.loads(row["body"]) for row in db.execute("SELECT * FROM weaknesses")}
            selection = select(materials, history, weaknesses, local_day(self.clock()), payload.get("target"))
            if operation == "select" or selection["primary"] is None:
                return selection
            material = {k: v for k, v in selection["primary"].items() if k in {"id", "pattern", "purpose", "examples", "notes", "priority"}}
            secondary = selection.get("secondary")
            session = {"id": uuid.uuid4().hex, "primary": material["id"], "material": material, "secondary": secondary, "purpose": selection["purpose"], "reason": selection["reason"], "synthetic": bool(payload.get("synthetic")), "stage": "question", "revision": 0}
            db.execute("INSERT INTO sessions VALUES (?,?,?,?)", (session["id"], "Active", encoded(session), self.clock()))
            return session
        if operation == "preview_migration":
            return migration.preview(db, payload)
        if operation == "accept_migration":
            return migration.accept(self, db, payload)
        if operation == "preview_repair":
            return repair.preview(self, db, payload)
        if operation == "apply_repair":
            return repair.apply(self, db, payload)
        if operation == "diagnostics":
            return {"project": json.loads((self.root / "data/project.json").read_text()), "integrity": db.execute("PRAGMA integrity_check").fetchone()[0], "weaknesses": [json.loads(row[0]) for row in db.execute("SELECT body FROM weaknesses")], "accepted_sessions": self._accepted(db), "repairs": [json.loads(row[0]) for row in db.execute("SELECT body FROM repairs ORDER BY rowid")], "legacy": [{"kind": row["kind"], "id": row["id"], "body": json.loads(row["body"])} for row in db.execute("SELECT * FROM legacy")]}
        if operation in {"resume", "pause", "question", "answer", "assess", "feedback", "retry", "correct", "history", "cue"}:
            return self._session_operation(db, operation, payload)
        if operation in {"backup", "export"}:
            return self._backup(db)
        raise PracticeError("unknown operation: " + operation)

    def _session(self, db: sqlite3.Connection, payload: Dict[str, Any]) -> Dict[str, Any]:
        if payload.get("session_id"):
            row = db.execute("SELECT * FROM sessions WHERE id=?", (payload["session_id"],)).fetchone()
        else:
            row = db.execute("SELECT * FROM sessions WHERE status!='Applied'").fetchone()
        if not row:
            raise PracticeError("no matching session")
        return {**json.loads(row["body"]), "status": row["status"]}

    def _events(self, db: sqlite3.Connection, session_id: str) -> Any:
        return [{"kind": row["kind"], "at": row["at"], **json.loads(row["body"])} for row in db.execute("SELECT * FROM events WHERE session_id=? ORDER BY seq", (session_id,))]

    def _event(self, db: sqlite3.Connection, session_id: str, kind: str, value: Dict[str, Any]) -> None:
        db.execute("INSERT INTO events(session_id,kind,body,at) VALUES (?,?,?,?)", (session_id, kind, encoded(value), self.clock()))

    def _session_operation(self, db: sqlite3.Connection, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        session = self._session(db, payload)
        events = self._events(db, session["id"])
        if operation in {"resume", "history"}:
            result = db.execute("SELECT * FROM results WHERE session_id=?", (session["id"],)).fetchone()
            return {**session, "events": events, "result": json.loads(result["body"]) if result else None, "finish_operation_id": result["operation_id"] if result else None, "finalization_request": json.loads(result["body"]).get("finalization_request") if result else None}
        if session["status"] in {"Applied", "Finalizing"}:
            raise PracticeError("session is immutable or finalizing")
        if "expected_revision" in payload and payload["expected_revision"] != session.get("revision", 0):
            raise PracticeError("session revision conflict; resume before writing")
        value: Dict[str, Any] = {}
        if operation == "pause":
            session["status"] = "Paused"
        elif operation == "cue":
            if payload.get("target", session["primary"]) != session["primary"] or payload.get("scope") not in {"target", "language", "unknown"} or not payload.get("text"):
                raise PracticeError("cue requires primary target, scope and text")
            value = {"target": session["primary"], "scope": payload["scope"], "text": payload["text"]}
            self._event(db, session["id"], "cue", value)
            if not session["synthetic"] or json.loads((self.root / "data/project.json").read_text())["test_mode"]:
                db.execute("INSERT OR REPLACE INTO activity VALUES (?,?,?)", (session["primary"], self.clock(), "cue-upper-bound"))
        elif operation == "question":
            if session["stage"] not in {"question", "ready"}:
                raise PracticeError("save the outstanding answer, assessment and feedback first")
            if len([e for e in events if e["kind"] == "question"]) >= 6:
                raise PracticeError("situation budget exhausted")
            for field in ("text", "context"):
                if not isinstance(payload.get(field), str) or not payload[field].strip():
                    raise PracticeError("question requires concrete text and context")
            target = payload.get("target", session["primary"])
            if not db.execute("SELECT 1 FROM materials WHERE id=?", (target,)).fetchone():
                raise PracticeError("unknown target")
            if target != session["primary"]:
                if any(e["kind"] == "question" and e["target"] != session["primary"] for e in events):
                    raise PracticeError("only one secondary retrieval")
            if target != session["primary"] and (not session.get("secondary") or target != session["secondary"]["id"]):
                raise PracticeError("secondary must be the pinned due review candidate")
            kind = payload.get("kind", "ordinary")
            if kind not in {"ordinary", "end"} or payload.get("hints", "none") not in {"none", "target", "language", "unknown"}:
                raise PracticeError("invalid question evidence")
            if any(e["kind"] == "question" and e["probe"] == "end" for e in events):
                raise PracticeError("end retrieval is the final situation")
            if kind == "end" and (payload.get("hints", "none") != "none" or not payload.get("new_context", True) or any(e["kind"] == "question" and e["context"] == payload["context"] for e in events)):
                raise PracticeError("end retrieval requires an unprompted new context")
            if kind == "end" and (target != session["primary"] or any(e["kind"] == "question" and e["probe"] == "end" for e in events)):
                raise PracticeError("only one primary end retrieval")
            previous = db.execute("SELECT at FROM activity WHERE id=?", (target,)).fetchone()
            delayed: Optional[bool] = None
            if previous and previous[0]:
                delayed = elapsed(self.clock(), previous[0]) and not any(e["kind"] == "cue" and e["target"] == target for e in events)
            value = {"id": uuid.uuid4().hex, "text": payload["text"], "context": payload["context"], "target": target, "probe": kind, "delayed": delayed, "new_context": payload.get("new_context", True), "hints": payload.get("hints", "none")}
            self._event(db, session["id"], "question", value)
            session.update(stage="answer", question_id=value["id"], retry_of=None)
        elif operation == "retry":
            if session["stage"] != "ready":
                raise PracticeError("feedback must be saved before retry")
            session.update(stage="answer", retry_of=session["attempt_id"])
        elif operation == "answer":
            if session["stage"] != "answer" or payload.get("question_id") != session.get("question_id"):
                raise PracticeError("wrong question or session stage")
            if not isinstance(payload.get("text"), str) or not payload["text"].strip():
                raise PracticeError("answer text is required")
            question = next(e for e in events if e["kind"] == "question" and e["id"] == payload["question_id"])
            value = {"id": uuid.uuid4().hex, "question_id": question["id"], "text": payload["text"], "retry_of": session.get("retry_of")}
            self._event(db, session["id"], "answer", value)
            if not session["synthetic"] or json.loads((self.root / "data/project.json").read_text())["test_mode"]:
                db.execute("INSERT OR REPLACE INTO activity VALUES (?,?,?)", (question["target"], self.clock(), "practice-upper-bound"))
            session.update(stage="assessment", attempt_id=value["id"])
        elif operation in {"assess", "feedback"}:
            stage = "assessment" if operation == "assess" else "feedback"
            if session["stage"] != stage or payload.get("attempt_id") != session.get("attempt_id"):
                raise PracticeError("wrong attempt or session stage")
            if operation == "assess":
                for field in ("target", "expression"):
                    if payload.get(field) not in {"pass", "fail", "unknown"}:
                        raise PracticeError("assessment requires explicit two-axis outcomes")
                if payload.get("hints", "none") not in {"none", "target", "language", "unknown"} or not payload.get("reason"):
                    raise PracticeError("assessment requires hint scope and evidence reason")
                observations = deepcopy(payload.get("weaknesses", []))
                if not isinstance(observations, list):
                    raise PracticeError("weaknesses must be opportunities array")
                for observation in observations:
                    if not isinstance(observation, dict) or any(not isinstance(observation.get(k), str) or not observation[k].strip() for k in ("key", "condition", "rule", "deviation")) or observation.get("scope") not in {"global", "structure"} or observation.get("outcome") not in {"pass", "fail", "unknown"} or not isinstance(observation.get("blocking"), bool) or observation.get("hints", "none") not in {"none", "target", "language", "unknown"}:
                        raise PracticeError("opportunity needs specific rule identity, condition, deviation, scope, blocking and outcome")
                    previous = db.execute("SELECT at FROM rule_activity WHERE key=?", (observation["key"],)).fetchone()
                    observation["previous_at"] = previous[0] if previous else None
                    if not session["synthetic"] or json.loads((self.root / "data/project.json").read_text())["test_mode"]:
                        db.execute("INSERT OR REPLACE INTO rule_activity VALUES (?,?)", (observation["key"], self.clock()))
                value = {"attempt_id": payload["attempt_id"], "target": payload["target"], "expression": payload["expression"], "hints": payload.get("hints", "none"), "reason": payload["reason"], "extension": bool(payload.get("extension")), "weaknesses": observations}
                session["stage"] = "feedback"
            else:
                if payload.get("hint", "none") not in {"none", "target", "language", "unknown"}:
                    raise PracticeError("invalid feedback hint scope")
                if not payload.get("text"):
                    raise PracticeError("feedback text is required")
                value = {"attempt_id": payload["attempt_id"], "text": payload["text"], "hint": payload.get("hint", "none")}
                session["stage"] = "ready"
                if value["hint"] != "none" and (not session["synthetic"] or json.loads((self.root / "data/project.json").read_text())["test_mode"]):
                    answer = next(e for e in events if e["kind"] == "answer" and e["id"] == payload["attempt_id"])
                    question = next(e for e in events if e["kind"] == "question" and e["id"] == answer["question_id"])
                    db.execute("INSERT OR REPLACE INTO activity VALUES (?,?,?)", (question["target"], self.clock(), "cue-upper-bound"))
                    assessment: Any = next((e for e in reversed(events) if e["kind"] == "assess" and e["attempt_id"] == payload["attempt_id"]), {})
                    for observation in assessment.get("weaknesses", []):
                        if not session["synthetic"] or json.loads((self.root / "data/project.json").read_text())["test_mode"]:
                            db.execute("INSERT OR REPLACE INTO rule_activity VALUES (?,?)", (observation["key"], self.clock()))
            self._event(db, session["id"], operation, value)
        elif operation == "correct":
            if not payload.get("text") or not payload.get("reason") or not any(e["kind"] == "answer" and e["id"] == payload.get("attempt_id") for e in events):
                raise PracticeError("correction needs original attempt, text and reason")
            if session["stage"] not in {"assessment", "feedback", "ready"}:
                raise PracticeError("resolve the outstanding answer before correcting another attempt")
            if session["stage"] in {"assessment", "feedback"} and payload["attempt_id"] != session.get("attempt_id"):
                raise PracticeError("complete the current attempt before correcting an earlier one")
            original = next(e for e in events if e["kind"] == "answer" and e["id"] == payload["attempt_id"])
            session["question_id"] = original["question_id"]
            value = {"attempt_id": payload["attempt_id"], "text": payload["text"], "reason": payload["reason"]}
            self._event(db, session["id"], "correction", value)
            session.update(stage="assessment", attempt_id=payload["attempt_id"])
        session["revision"] = session.get("revision", 0) + 1
        db.execute("UPDATE sessions SET status=?,body=? WHERE id=?", (session["status"], encoded(session), session["id"]))
        return {**(value or session), "revision": session["revision"]}

    def _backup(self, db: sqlite3.Connection) -> Dict[str, Any]:
        destination = self.root / "data/backups" / uuid.uuid4().hex
        destination.mkdir(parents=True)
        # A second reader obtains a committed WAL snapshot while the caller holds
        # the writer lock. Backing up the writer itself would wait on that lock.
        with closing(sqlite3.connect(str(self.root / "data/practice.sqlite3"))) as reader, closing(sqlite3.connect(str(destination / "practice.sqlite3"))) as backup:
            reader.backup(backup)
            if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise PracticeError("backup integrity check failed")
        for relative in ("materials", "data/imports", "data/requests", "data/project.json", ".codex/config.toml"):
            source = self.root / relative
            target = destination / relative
            if source.is_dir():
                shutil.copytree(source, target)
            elif source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        plugin = Path(__file__).resolve().parents[2]
        shutil.copytree(plugin, destination / "runtime", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in ("schemas", "docs/adr", "docs/material-source-format.md"):
            source = self.root / name
            if source.is_dir():
                shutil.copytree(source, destination / name)
            elif source.is_file():
                (destination / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination / name)
        hashes = {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest() for path in destination.rglob("*") if path.is_file()}
        atomic_json(destination / "manifest.json", {"files": hashes, "schema": 1})
        verify(destination)
        return {"checkpoint": str(destination), "files": len(hashes)}

    def _accepted(self, db: sqlite3.Connection) -> Any:
        return repair.accepted(db)

    def _compute_result(self, db: sqlite3.Connection, session: Dict[str, Any]) -> Any:
        events = self._events(db, session["id"])
        result: Dict[str, Any] = {"session_id": session["id"], "policy": POLICY, "synthetic": session.get("synthetic", False), "purpose": session.get("purpose", "unknown"), "primary": session["primary"], "frames": {}}
        for target in sorted({e["target"] for e in events if e["kind"] == "question"}):
            questions = {e["id"]: e for e in events if e["kind"] == "question" and e["target"] == target}
            answers = [e for e in events if e["kind"] == "answer" and e["question_id"] in questions]
            assessments: Dict[str, Any] = {}
            corrections: Dict[str, Any] = {}
            feedbacks: Dict[str, Any] = {}
            for event in events:
                if event["kind"] == "correction":
                    corrections[event["attempt_id"]] = event
                    assessments.pop(event["attempt_id"], None)
                elif event["kind"] == "assess":
                    assessments[event["attempt_id"]] = event
                elif event["kind"] == "feedback":
                    feedbacks[event["attempt_id"]] = event
            productions: Any = []
            for answer in answers:
                assessment = assessments.get(answer["id"], {"target": "unknown", "expression": "unknown", "hints": "unknown"})
                question = questions[answer["question_id"]]
                target_independent = not answer["retry_of"] and assessment["hints"] in {"none", "language"} and question["hints"] in {"none", "language"}
                independent = target_independent and assessment["hints"] == question["hints"] == "none"
                production = {"attempt_id": answer["id"], "text": corrections.get(answer["id"], answer)["text"], "original_text": answer["text"], "context": question["context"], "question_id": question["id"], "first": not answer["retry_of"], "target": assessment["target"], "expression": assessment["expression"], "independent": independent, "target_independent": target_independent, "probe": question["probe"], "delayed": not productions and question["delayed"] is True and question["new_context"] and independent and assessment["expression"] == assessment["target"] == "pass", "new_context": question["new_context"], "extension": assessment.get("extension", False), "hints": assessment["hints"], "question_hints": question["hints"], "feedback_hint": feedbacks.get(answer["id"], {}).get("hint", "none"), "weaknesses": assessment.get("weaknesses", []), "reason": assessment.get("reason", "missing assessment"), "at": answer["at"], "time_source": "platform-received-upper-bound"}
                production["delayed_eligible"] = not productions and question["delayed"] is True and question["new_context"] and independent
                productions.append(production)
            if productions:
                result["frames"][target] = frame(productions, target == session["primary"])
        progress = {row["id"]: json.loads(row["body"]) for row in db.execute("SELECT * FROM progress")}
        weaknesses = {row["key"]: json.loads(row["body"]) for row in db.execute("SELECT * FROM weaknesses")}
        marker = json.loads((self.root / "data/project.json").read_text())
        if result["synthetic"] and not marker["test_mode"]:
            return result, {"progress": {}, "weaknesses": weaknesses}
        history = [r for r in self._accepted(db) if marker["test_mode"] or not r.get("synthetic")]
        changes, ledger = project(result, history, progress, weaknesses)
        return result, {"progress": changes, "weaknesses": ledger}

    def _finish(self, request: Dict[str, Any]) -> Dict[str, Any]:
        identity = request.get("operation_id")
        if not isinstance(identity, str) or not identity:
            raise PracticeError("operation_id is required")
        request_hash = digest({"operation": "finish", "payload": request.get("payload", {})})
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT * FROM operations WHERE id=?", (identity,)).fetchone()
            if prior:
                if prior["hash"] != request_hash:
                    raise PracticeError("operation identity conflict")
                return json.loads(prior["result"])
            session = self._session(db, request.get("payload", {}))
            frozen = db.execute("SELECT * FROM results WHERE session_id=?", (session["id"],)).fetchone()
            if frozen:
                if frozen["operation_id"] != identity or frozen["request_hash"] != request_hash:
                    raise PracticeError("resume using the frozen finalization identity")
            else:
                result, plan = self._compute_result(db, session)
                result["finalization_request"] = deepcopy(request)
                db.execute("INSERT INTO results VALUES (?,?,?,?,?)", (session["id"], encoded(result), encoded(plan), identity, request_hash))
                db.execute("UPDATE sessions SET status='Finalizing' WHERE id=?", (session["id"],))
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT * FROM operations WHERE id=?", (identity,)).fetchone()
            if prior:
                if prior["hash"] != request_hash:
                    raise PracticeError("operation identity conflict")
                return json.loads(prior["result"])
            checkpoint = self._backup(db)
            frozen = db.execute("SELECT * FROM results WHERE session_id=?", (session["id"],)).fetchone()
            result, plan = json.loads(frozen["body"]), json.loads(frozen["plan"])
            for target, change in plan["progress"].items():
                actual = json.loads(db.execute("SELECT body FROM progress WHERE id=?", (target,)).fetchone()[0])
                if actual != change["before"]:
                    raise PracticeError("frozen finalization plan conflict")
                db.execute("UPDATE progress SET body=? WHERE id=?", (encoded(change["after"]), target))
            for key, body in plan["weaknesses"].items():
                db.execute("INSERT OR REPLACE INTO weaknesses VALUES (?,?)", (key, encoded(body)))
            db.execute("UPDATE sessions SET status='Applied' WHERE id=?", (session["id"],))
            response = {"session_id": session["id"], "result": result, "changes": plan["progress"], **checkpoint}
            db.execute("INSERT INTO operations VALUES (?,?,?)", (identity, request_hash, encoded(response)))
        with closing(self._connect()) as db:
            if db.execute("SELECT status FROM sessions WHERE id=?", (session["id"],)).fetchone()[0] != "Applied":
                raise PracticeError("finalization readback failed")
        return response
