import hashlib
import json
import re
from typing import Any, Dict


def encoded(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def validate(pack: Dict[str, Any]) -> None:
    if not isinstance(pack, dict) or set(pack) != {"format", "source", "items"}:
        raise ValueError("pack requires only format, source, items")
    if pack["format"] != "sentence-materials/v1":
        raise ValueError("unsupported material format")
    def text(value: Any) -> None:
        if not isinstance(value, str) or not value.strip() or value.strip() in {"—", "-", "待補"}:
            raise ValueError("material text must be nonempty, without placeholders")
    text(pack["source"])
    if not isinstance(pack["items"], list) or not pack["items"]:
        raise ValueError("at least one material is required")
    ids = set()
    for item in pack["items"]:
        if not isinstance(item, dict) or set(item) - {"id", "pattern", "purpose", "examples", "notes", "priority"}:
            raise ValueError("unexpected material fields")
        for key in ("pattern", "purpose"):
            text(item.get(key))
        if not isinstance(item.get("examples"), list) or not item["examples"]:
            raise ValueError("examples must be a nonempty array")
        for example in item["examples"]:
            text(example)
        if "notes" in item:
            text(item["notes"])
        if item.get("priority", "High") not in {"Core", "High", "Useful"}:
            raise ValueError("invalid priority")
        if "id" in item:
            identifier = item["id"]
            if not isinstance(identifier, str) or not re.fullmatch(r"S[0-9]{3,}", identifier) or identifier in ids:
                raise ValueError("invalid or duplicate local material ID")
            ids.add(identifier)


def material_hash(item: Dict[str, Any]) -> str:
    return digest({key: value for key, value in item.items() if key != "id"})


def load_json(text: str) -> Any:
    def pairs(values: Any) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    def constant(value: str) -> None:
        raise ValueError("non-finite JSON number: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
