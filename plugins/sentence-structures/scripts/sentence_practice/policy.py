"""Deterministic policy; qualitative observations are supplied with evidence."""
from copy import deepcopy
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Tuple

POLICY = "local-practice-v1"
STATES = ["New", "Learning", "Usable", "Automatic"]


def local_day(at: str) -> str:
    instant = datetime.fromisoformat(at)
    if instant.tzinfo is None:
        raise ValueError("clock must have a timezone")
    return instant.astimezone(ZoneInfo("Asia/Taipei")).date().isoformat()


def elapsed(later: str, earlier: Any) -> bool:
    if not earlier:
        return False
    try:
        a, b = datetime.fromisoformat(later), datetime.fromisoformat(earlier)
        return a.tzinfo is not None and b.tzinfo is not None and (a - b).total_seconds() >= 86400
    except (TypeError, ValueError):
        return False


def succeeded(p: Dict[str, Any]) -> bool:
    return p["independent"] and p["target"] == p["expression"] == "pass"


def frame(productions: List[Dict[str, Any]], primary: bool) -> Dict[str, Any]:
    probe = next((p for p in productions if p["probe"] == "end" and p["first"]), None) if primary else productions[0]
    outcome = "not_tested"
    if probe:
        outcome = "pass" if succeeded(probe) else ("fail" if "fail" in {probe["target"], probe["expression"]} else "unknown")
        if primary and not probe["new_context"]:
            outcome = "unknown"
    first = productions[0]
    return {"productions": productions, "independent_uses": sum(succeeded(p) for p in productions),
            "probe": outcome, "first": first["target"] if first["target_independent"] else "unknown",
            "first_full": "pass" if succeeded(first) else "unknown", "full_success": outcome == "pass"}


def update_weaknesses(history: List[Dict[str, Any]], current: Dict[str, Any], existing: Dict[str, Any]) -> Dict[str, Any]:
    ledger = deepcopy(existing)
    session_id = current["session_id"]
    window = {r["session_id"] for r in (history + [current])[-10:]}
    opportunities: Dict[str, Any] = {}
    for target, item in current["frames"].items():
        for production in item["productions"]:
            if not production["first"]:
                continue
            for observation in production["weaknesses"]:
                key = observation["key"]
                candidate = {**observation, "session_id": session_id, "at": production["at"],
                             "context": production["context"], "target": target,
                             "independent": production["independent"] and observation.get("hints", "none") == "none", "previous_at": observation.get("previous_at")}
                # First applicable opportunity only; a confirmed occurrence wins.
                if key not in opportunities or (candidate["outcome"] == "fail" and candidate["independent"]):
                    opportunities[key] = candidate
    for key, opportunity in opportunities.items():
        entry = ledger.setdefault(key, {"key": key, "status": "observed", "occurrences": [], "opportunities": [], "resolutions": []})
        for field in ("condition", "rule", "deviation", "scope", "blocking"):
            entry[field] = opportunity[field]
        previous = opportunity.get("previous_at")
        opportunity["delayed"] = elapsed(opportunity["at"], previous)
        entry["opportunities"].append(opportunity)
        failed = opportunity["outcome"] == "fail" and opportunity["independent"]
        if failed:
            entry["occurrences"].append(opportunity)
            entry["last_occurrence"] = opportunity["at"]
            count = len({o["session_id"] for o in entry["occurrences"] if o["session_id"] in window})
            if entry["status"] in {"active", "resolved"} or count >= 2:
                entry["status"] = "active"
            entry["resolution_window"] = []
        elif opportunity["outcome"] == "pass" and opportunity["independent"] and entry["status"] == "active":
            successes = entry.setdefault("resolution_window", [])
            successes.append(opportunity)
            if len({o["session_id"] for o in successes}) >= 2 and len({o["context"] for o in successes}) >= 2 and any(o["delayed"] for o in successes):
                entry["status"] = "resolved"
                entry["resolutions"].append({"session_id": session_id, "at": opportunity["at"], "evidence": deepcopy(successes)})
    return ledger


def project(current: Dict[str, Any], history: List[Dict[str, Any]], progress: Dict[str, Any], weaknesses: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    ledger = update_weaknesses(history, current, weaknesses)
    changes: Dict[str, Any] = {}
    for target, evidence in current["frames"].items():
        before = progress[target]
        after = deepcopy(before)
        relevant = [r["frames"][target] for r in history if target in r.get("frames", {})] + [evidence]
        local = [r["frames"][target] for r in history if r.get("policy") == POLICY and target in r.get("frames", {})] + [evidence]
        productions = [p for f in local for p in f["productions"]]
        passes = [p for p in productions if succeeded(p)]
        blockers = any(w.get("status") == "active" and w.get("blocking") and (w.get("scope") == "global" or any(o["target"] == target for o in w.get("opportunities", []))) for w in ledger.values())
        demote = len(relevant) >= 2 and all(f.get("first") == "fail" for f in relevant[-2:])
        state = before["state"]
        if demote:
            state = STATES[max(1, STATES.index(state) - 1)]
        elif state == "New":
            state = "Learning"
        elif evidence["full_success"] and not blockers:
            success_sessions = sum(f.get("independent_uses", 0) > 0 for f in local)
            delayed_sessions = sum(any(p["delayed"] and succeeded(p) for p in f["productions"]) for f in local)
            if state == "Learning" and success_sessions >= 2 and len(passes) >= 3 and len({p["context"] for p in passes}) >= 2 and delayed_sessions >= 1:
                state = "Usable"
            elif state == "Usable" and success_sessions >= 3 and delayed_sessions >= 2 and len(relevant) >= 2 and all(f.get("first_full") == "pass" for f in relevant[-2:]) and any(p["extension"] for p in passes):
                state = "Automatic"
        after["state"] = state
        after["uses"] += evidence["independent_uses"]
        after["sessions"] += int(evidence["independent_uses"] > 0)
        helped = any(p["hints"] != "none" or p["question_hints"] != "none" or p["feedback_hint"] != "none" for p in evidence["productions"])
        days = 2
        if helped or evidence["probe"] == "fail":
            days = 1 if state == "Learning" else 2
        elif evidence["probe"] == "pass":
            days = {"Learning": 3, "Usable": 7, "Automatic": 21}[state]
        after["last_practiced"] = evidence["productions"][-1]["at"]
        day = datetime.fromisoformat(local_day(after["last_practiced"])).date()
        after["next_review"] = (day + timedelta(days=days)).isoformat()
        changes[target] = {"before": before, "after": after}
    return changes, ledger
