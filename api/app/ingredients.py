from __future__ import annotations

from fastapi import HTTPException

from app.ml.model import class_names

# Friendly spellings → YOLO class names stored in best.pt
_ALIASES = {
    "cheese": "Cheeze",
    "parsley": "Parsely",
    "sausage": "Saus",
    "hotdog": "Saus",
    "calamansi": "LimeComG",
    "greencalamansi": "LimeComG",
    "yellowcalamansi": "LimeComY",
    "greenbellpepper": "GBellP",
    "greenbell": "GBellP",
    "redbellpepper": "RBellP",
    "redbell": "RBellP",
    "yellowbellpepper": "YBellP",
    "yellowbell": "YBellP",
    "greenpepper": "PepperG",
    "redpepper": "PepperR",
    "shrimpgroup": "ShrimGroup",
    "shrimps": "ShrimGroup",
    "eggplant": "EggPlant",
    "talong": "EggPlant",
}


def _key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def resolve_ingredient(raw: str, allowed: list[str] | None = None) -> str | None:
    text = raw.strip()
    if not text:
        return None
    names = allowed if allowed is not None else class_names()
    compact = _key(text)
    if not compact:
        return None

    by_key = {_key(name): name for name in names}
    if compact in by_key:
        return by_key[compact]

    alias = _ALIASES.get(compact)
    if alias and _key(alias) in by_key:
        return by_key[_key(alias)]
    return None


def canonicalize_ingredients(raw: list[str]) -> list[str]:
    allowed = class_names()
    canonical: list[str] = []
    unknown: list[str] = []
    seen: set[str] = set()

    for item in raw:
        resolved = resolve_ingredient(item, allowed)
        if resolved is None:
            unknown.append(item.strip() or item)
            continue
        if resolved not in seen:
            seen.add(resolved)
            canonical.append(resolved)

    if unknown:
        if len(unknown) == 1:
            detail = f'"{unknown[0]}" is not yet available.'
        else:
            preview = ", ".join(f'"{name}"' for name in unknown[:3])
            extra = f" (+{len(unknown) - 3} more)" if len(unknown) > 3 else ""
            detail = f"{preview}{extra} is not yet available."
        raise HTTPException(status_code=400, detail=detail)
    if not canonical:
        raise HTTPException(
            status_code=400,
            detail="Add at least one ingredient from the detector list.",
        )
    return canonical
