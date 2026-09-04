from __future__ import annotations
from fastapi import HTTPException
from app.ml.model import class_names

# Roboflow names in best.pt → names shown in the UI and sent to Gemini.
# Class ids stay the same; this does not retrain the model.
DISPLAY_NAMES = {
    "Cheeze": "Cheese",
    "EggPlant": "Eggplant",
    "GBellP": "Green bell pepper",
    "LimeComG": "Green calamansi",
    "LimeComY": "Yellow calamansi",
    "Parsely": "Parsley",
    "PepperG": "Green pepper",
    "PepperR": "Red pepper",
    "RBellP": "Red bell pepper",
    "Saus": "Sausage",
    "ShrimGroup": "Shrimp",
    "YBellP": "Yellow bell pepper",
}

# Human spellings → Roboflow names stored in best.pt
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
    "shimp": "Shrimp",
    "eggplant": "EggPlant",
    "talong": "EggPlant",
}


def _key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def display_name(roboflow: str) -> str:
    return DISPLAY_NAMES.get(roboflow, roboflow)


def display_class_names() -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for name in class_names():
        pretty = display_name(name)
        if pretty not in seen:
            seen.add(pretty)
            names.append(pretty)
    return names


def resolve_ingredient(raw: str, allowed: list[str] | None = None) -> str | None:
    """Return the Roboflow class name, or None if it is not in the detector."""
    text = raw.strip()
    if not text:
        return None
    names = allowed if allowed is not None else class_names()
    compact = _key(text)
    if not compact:
        return None

    by_roboflow = {_key(name): name for name in names}
    if compact in by_roboflow:
        return by_roboflow[compact]

    by_display = {_key(display_name(name)): name for name in names}
    if compact in by_display:
        return by_display[compact]

    alias = _ALIASES.get(compact)
    if not alias:
        return None
    if _key(alias) in by_roboflow:
        return by_roboflow[_key(alias)]
    if _key(alias) in by_display:
        return by_display[_key(alias)]
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
        pretty = display_name(resolved)
        if pretty not in seen:
            seen.add(pretty)
            canonical.append(pretty)

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
