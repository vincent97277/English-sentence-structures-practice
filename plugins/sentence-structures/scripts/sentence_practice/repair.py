"""Append-only dictation corrections and deterministic projection repair."""
import json
import uuid
from copy import deepcopy
from typing import Any, Dict
from .materials import digest, encoded
from .policy import POLICY, frame, project


def accepted(db: Any) -> Any:
    results = [json.loads(row[0]) for row in db.execute("SELECT r.body FROM results r JOIN sessions s ON s.id=r.session_id WHERE s.status='Applied' ORDER BY s.rowid")]
    for row in db.execute("SELECT body FROM repairs ORDER BY rowid"):
        repair = json.loads(row[0])
        if repair.get("status") == "Applied":
            replacements = repair["effective_results"]
            results = [replacements.get(r["session_id"], r) for r in results]
    return results


def basis(db: Any) -> str:
    return digest({table: [dict(row) for row in db.execute("SELECT * FROM " + table + " ORDER BY rowid")] for table in ("progress", "results", "weaknesses", "repairs", "sessions")})


def preview(api: Any, db: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
    if db.execute("SELECT 1 FROM sessions WHERE status!='Applied'").fetchone():
        raise ValueError("finish the active session before planning a repair")
    if not payload.get("text") or not payload.get("reason"):
        raise ValueError("post-finalization correction needs text and reason")
    identity = payload["session_id"]
    history = accepted(db)
    result = next((r for r in history if r["session_id"] == identity), None)
    if result is None or result.get("policy") != POLICY:
        raise ValueError("legacy summaries lack answer-level evidence; automatic repair unavailable")
    assessment = payload.get("assessment", {})
    if any(assessment.get(k) not in {"pass", "fail", "unknown"} for k in ("target", "expression")) or not assessment.get("reason"):
        raise ValueError("repair needs evidence-based two-axis reassessment")
    effective = deepcopy(result)
    target = None
    original = None
    for identifier, item in effective["frames"].items():
        for production in item["productions"]:
            if production["attempt_id"] == payload["attempt_id"]:
                target, original = identifier, deepcopy(production)
                production.update(text=payload["text"], target=assessment["target"], expression=assessment["expression"], reason=assessment["reason"])
                if "weaknesses" in assessment:
                    if assessment["weaknesses"]:
                        raise ValueError("repair may remove ASR-derived observations; new observations need fresh practice")
                    production["weaknesses"] = []
                production["delayed"] = production.get("delayed_eligible", False) and production["target"] == production["expression"] == "pass"
        if target == identifier:
            effective["frames"][identifier] = frame(item["productions"], identifier == effective["primary"])
    if target is None:
        raise ValueError("unknown original answer")
    history = [effective if r["session_id"] == identity else r for r in history]
    current = {row["id"]: json.loads(row["body"]) for row in db.execute("SELECT * FROM progress")}
    replay = deepcopy(current)
    # Earliest frozen before-image is the untouched migration/new-material base.
    baseline: Dict[str, Any] = {}
    for row in db.execute("SELECT plan FROM results r JOIN sessions s ON s.id=r.session_id WHERE s.status='Applied' ORDER BY s.rowid"):
        for identifier, change in json.loads(row[0]).get("progress", {}).items():
            baseline.setdefault(identifier, change["before"])
    replay.update(baseline)
    ledger: Dict[str, Any] = {}
    prior: Any = []
    marker = json.loads((api.root / "data/project.json").read_text())
    for item in history:
        if item.get("policy") == POLICY and (marker["test_mode"] or not item.get("synthetic")):
            changes, ledger = project(item, prior, replay, ledger)
            for identifier, change in changes.items():
                replay[identifier] = change["after"]
        if marker["test_mode"] or not item.get("synthetic"):
            prior.append(item)
    plan = {identifier: {"before": before, "after": replay[identifier]} for identifier, before in current.items() if before != replay[identifier]}
    correction_id = uuid.uuid4().hex
    correction = {"id": correction_id, "status": "Proposed", "session_id": identity, "attempt_id": payload["attempt_id"], "original": original, "text": payload["text"], "reason": payload["reason"], "at": api.clock(), "assessment": assessment, "changes": plan, "weaknesses": ledger, "effective_results": {r["session_id"]: r for r in history}, "basis": basis(db)}
    db.execute("INSERT INTO repairs VALUES (?,?)", (correction_id, encoded(correction)))
    correction["basis"] = basis(db)
    # Basis excludes this proposal itself on acceptance via explicit comparison.
    return {"repair_id": correction_id, "changes": plan, "corrected_result": effective, "confirmation_required": True}


def apply(api: Any, db: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
    row = db.execute("SELECT body FROM repairs WHERE id=?", (payload["repair_id"],)).fetchone()
    if row is None or not payload.get("confirmed"):
        raise ValueError("explicit confirmation of an existing repair is required")
    proposal = json.loads(row[0])
    prior = db.execute("SELECT body FROM repairs WHERE id=?", (payload["repair_id"] + ":applied",)).fetchone()
    if prior:
        return json.loads(prior[0])["response"]
    if db.execute("SELECT 1 FROM sessions WHERE status!='Applied'").fetchone():
        raise ValueError("finish active work before applying repair")
    # Any accepted work/import/repair after the proposal requires a new plan.
    body_rows = [dict(row) for row in db.execute("SELECT * FROM repairs ORDER BY rowid") if row["id"] != payload["repair_id"]]
    actual = {table: [dict(row) for row in db.execute("SELECT * FROM " + table + " ORDER BY rowid")] for table in ("progress", "results", "weaknesses", "sessions")}
    actual["repairs"] = body_rows
    if digest(actual) != proposal["basis"]:
        raise ValueError("repair proposal is stale; generate a new impact plan")
    checkpoint = api._backup(db)
    for identifier, change in proposal["changes"].items():
        db.execute("UPDATE progress SET body=? WHERE id=?", (encoded(change["after"]), identifier))
    db.execute("DELETE FROM weaknesses")
    for key, weakness in proposal["weaknesses"].items():
        db.execute("INSERT INTO weaknesses VALUES (?,?)", (key, encoded(weakness)))
    response = {"repair_id": proposal["id"], "repaired": True, "changes": proposal["changes"], **checkpoint}
    applied = {**proposal, "status": "Applied", "response": response}
    db.execute("INSERT INTO repairs VALUES (?,?)", (proposal["id"] + ":applied", encoded(applied)))
    return response
