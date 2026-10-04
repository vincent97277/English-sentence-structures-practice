from typing import Any, Dict, List


def select(materials: List[Dict[str, Any]], history: List[Dict[str, Any]], weaknesses: Dict[str, Any], day: str, target: Any = None) -> Dict[str, Any]:
    active = [m for m in materials if m["active"]]
    if target:
        chosen = next((m for m in active if m["id"] == target), None)
        if chosen is None:
            raise ValueError("requested material is unavailable")
        return {"primary": chosen, "purpose": "new" if chosen["state"] == "New" else "review", "reason": "explicit target", "secondary": None}
    due = [m for m in active if m.get("next_review") and m["next_review"] <= day and m["state"] != "New"]
    new = [m for m in active if m["state"] == "New"]
    def blocked(identifier: str) -> bool:
        return any(w.get("status") == "active" and w.get("blocking") and (w.get("scope") == "global" or any(o.get("target") == identifier for o in w.get("opportunities", []))) for w in weaknesses.values())
    due.sort(key=lambda m: (m["next_review"], not blocked(m["id"]), m["id"]))
    new.sort(key=lambda m: ({"Core": 0, "High": 1, "Useful": 2}[m["priority"]], m["id"]))
    force_new = len(history) >= 2 and all(r.get("purpose") == "review" for r in history[-2:]) and bool(new)
    candidates = new if force_new or not due else due
    if not candidates:
        return {"primary": None, "next_due": min((m["next_review"] for m in active if m.get("next_review")), default=None), "reason": "nothing due or new"}
    last = history[-1].get("primary") if history else None
    varied = [m for m in candidates if m["id"] != last]
    primary = (varied or candidates)[0]
    secondary = next((m for m in due if m["id"] != primary["id"]), None)
    return {"primary": primary, "secondary": secondary, "purpose": "new" if primary["state"] == "New" else "review", "reason": "new after two reviews" if force_new else ("due review" if due else "new material")}
