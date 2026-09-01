from __future__ import annotations

import json
import os
import re
from typing import Any

from app.config import gemini_model

_PLACEHOLDER_KEYS = {
    "",
    "paste_your_key_here",
    "your-api-key",
    "YOUR_API_KEY",
}


def llm_configured() -> bool:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return bool(key) and key not in _PLACEHOLDER_KEYS


def _client():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key in _PLACEHOLDER_KEYS:
        return None
    from google import genai

    return genai.Client(api_key=api_key)


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if fenced:
        cleaned = fenced.group(1).strip()
    return json.loads(cleaned)


def _complete(prompt: str, max_tokens: int) -> dict[str, Any]:
    from google.genai import types

    client = _client()
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is not set")

    # 2.5 Flash spends max_output_tokens on thinking unless budget is 0,
    # which truncated JSON mid-string (json.JSONDecodeError).
    response = client.models.generate_content(
        model=gemini_model(),
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.6,
            max_output_tokens=max_tokens,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    text = response.text or "{}"
    try:
        return _parse_json(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini returned invalid JSON: {exc}") from exc


def generate_recipes(ingredients: list[str]) -> list[dict[str, str]]:
    joined = ", ".join(ingredients)
    prompt = f"""
You are an expert Filipino home cook.
Given these scanned ingredients: {joined}

Suggest exactly 5 authentic Filipino household recipes that use these ingredients.

You may assume pantry staples the camera cannot see: rice, water, cooking oil,
salt, soy sauce (toyo), and vinegar (suka).
Do not add any other meat, seafood, vegetable, or fruit that was not listed.

Rules:
- Recipe names only (e.g. "Chicken Adobo"), no extra ingredients in the title
- Avoid near-duplicates (e.g. Pesang Isda and Pesa)
- One short sentence description each

Return JSON only:
{{"recipes": [{{"name": "Dish Name", "description": "One sentence."}}]}}
"""
    data = _complete(prompt, max_tokens=4096)
    recipes = data.get("recipes") or []
    cleaned = []
    for item in recipes[:5]:
        name = str(item.get("name", "")).strip()
        description = str(item.get("description", "")).strip()
        if name:
            cleaned.append({"name": name, "description": description})
    if len(cleaned) < 1:
        raise RuntimeError("Model returned no recipes")
    return cleaned


def generate_steps(name: str, ingredients: list[str]) -> dict[str, Any]:
    joined = ", ".join(ingredients) if ingredients else "common Filipino pantry items"
    prompt = f"""
You are an expert Filipino home cook.
Create a home-kitchen recipe for "{name}" that prominently uses: {joined}.

You may assume pantry staples the camera cannot see: rice, water, cooking oil,
salt, soy sauce (toyo), and vinegar (suka).
Do not add any other meat, seafood, vegetable, or fruit that was not listed.

Return JSON only with this shape:
{{
  "name": "{name} (short English subtitle)",
  "servings": "1-2",
  "allergens": "list or None",
  "ingredients": ["quantity + item", "..."],
  "steps": [{{"title": "Step title", "detail": "What to do, including times."}}],
  "notes": ["optional tip"],
  "reference": ""
}}

Rules:
- Keep the dish name as "{name}" (subtitle in parentheses is ok)
- Required scanned ingredients must appear in the ingredients list, not marked optional
- Authentic Filipino household methods
- No markdown bullets inside strings
"""
    data = _complete(prompt, max_tokens=8192)
    steps = []
    for step in data.get("steps") or []:
        title = str(step.get("title", "")).strip()
        detail = str(step.get("detail", "")).strip()
        if title or detail:
            steps.append({"title": title or "Step", "detail": detail})
    return {
        "name": str(data.get("name") or name).strip(),
        "servings": str(data.get("servings") or "1-2").strip(),
        "allergens": str(data.get("allergens") or "None specified").strip(),
        "ingredients": [str(i).strip() for i in (data.get("ingredients") or []) if str(i).strip()],
        "steps": steps,
        "notes": [str(n).strip() for n in (data.get("notes") or []) if str(n).strip()],
        "reference": str(data.get("reference") or "").strip(),
    }
