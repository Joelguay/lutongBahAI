from __future__ import annotations

import json
import os
from typing import Any

from app.config import openai_model


def openai_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def _complete(prompt: str, max_tokens: int) -> dict[str, Any]:
    client = _client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not set")

    response = client.chat.completions.create(
        model=openai_model(),
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.6,
    )
    text = response.choices[0].message.content or "{}"
    return json.loads(text)


def generate_recipes(ingredients: list[str]) -> list[dict[str, str]]:
    joined = ", ".join(ingredients)
    prompt = f"""
You are an expert Filipino home cook.
Given these ingredients: {joined}

Suggest exactly 5 authentic Filipino household recipes that use these ingredients
(you may add pantry staples like rice, soy sauce, vinegar, garlic, oil, salt).

Rules:
- Recipe names only (e.g. "Chicken Adobo"), no extra ingredients in the title
- Avoid near-duplicates (e.g. Pesang Isda and Pesa)
- One short sentence description each

Return JSON only:
{{"recipes": [{{"name": "Dish Name", "description": "One sentence."}}]}}
"""
    data = _complete(prompt, max_tokens=800)
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
- Required ingredients must appear in the ingredients list, not marked optional
- Authentic Filipino household methods
- No markdown bullets inside strings
"""
    data = _complete(prompt, max_tokens=2000)
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
