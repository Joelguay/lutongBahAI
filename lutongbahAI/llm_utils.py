import re
import os
from cachetools import TTLCache
from openai import OpenAI
from dotenv import load_dotenv

# MERGE NOTE: Added load_dotenv() from the other developer's version.
# This makes local development easier by automatically loading your API key from a .env file.
load_dotenv()

# MERGE NOTE: Kept the improved OpenAI client initialization.
# This version checks if the API key exists and provides a clear error message
# if it's missing, which is much better than failing later.
_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Create a .env file with OPENAI_API_KEY=your_key or set it in your environment."
    )
client = OpenAI(api_key=_api_key)


# Caches (Identical in both versions)
recipe_cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour
steps_cache = TTLCache(maxsize=100, ttl=7200)   # 2 hours


# MERGE NOTE: Kept the corrected run_openai function.
# Your original version used 'max_completion_tokens', which is an outdated parameter.
# The other developer's version correctly uses 'max_tokens' for the current OpenAI library. This is a critical bug fix.
def run_openai(prompt, model="gpt-4.1", max_tokens=1200, log_tokens=False):
    """Call GPT-4.1 via OpenAI API with safer defaults."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens, # This is the corrected parameter name
            temperature = 0.6
        )
        result_text = response.choices[0].message.content.strip()

        if log_tokens:
            usage = response.usage
            print(f"Tokens used - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")

        return result_text
    except Exception as e:
        return f"Error: {str(e)}"

def generate_recipes(ingredients, use_cache=False, model="gpt-4.1", detection_json_text: str | None = None):
    """Generate 5 Filipino household recipes given ingredients.
    Optionally include raw detection JSON to give the model more context without changing output format.
    """
    cache_key = f"recipes_{','.join(sorted(ingredients))}"
    if use_cache and cache_key in recipe_cache:
        return recipe_cache[cache_key]

    # This is the new feature: adding extra context if available.
    detection_context = (f"\n\nRaw detection JSON for reference (do not change output format):\n{detection_json_text}" if detection_json_text else "")

    prompt = (
        f"You are an expert Filipino cook.\n"
        f"Given ingredients: {', '.join(ingredients)},\n"
        "suggest 5 Filipino household recipes that use all of these ingredients.\n"
        "For each recipe, provide a short description (1 sentence).\n"
        "Don't add ingredients to the recipe name. Only the recipe name(e.g. Chicken Adobo, not Chicken Adobo with Garlic and Ginger)\n"
        "Avoid repeating the same dish (e.g. Pesang isda & Pesa)\n"
        "Focus on authentic Filipino home recipes.\n"
        "Number them 1 to 5 in this format:\n"
        "Recipe 1: Recipe Name \nShort description.\n"
        "Recipe 2: Recipe Name \nShort description.\n"
        "Recipe 3: Recipe Name \nShort description.\n"
        "Recipe 4: Recipe Name \nShort description.\n"
        "Recipe 5: Recipe Name \nShort description."
        f"{detection_context}" # The new context is added here
    )

    result = run_openai(prompt, model=model, max_tokens=1200)

    if use_cache:
        recipe_cache[cache_key] = result

    return result

def _determine_primary_protein(ingredients):
    proteins = ["chicken", "egg", "fish", "Meat", "Milk", "Cheese", "ShrimGroup","Shrimp"]
    for ingredient in ingredients:
        for protein in proteins:
            if protein in ingredient.lower():
                return protein.capitalize()
    return None

def get_recipe_steps(recipe_name, required_ingredients=None, use_cache=False, model="gpt-4.1"):
    """Generate step-by-step instructions for a recipe."""
    cache_key = f"steps_{recipe_name.lower().strip()}_{','.join(sorted(required_ingredients or []))}"
    if use_cache and cache_key in steps_cache:
        return steps_cache[cache_key]
    
    primary_protein = _determine_primary_protein(required_ingredients or [])
    
    protein_instruction = ""
    if primary_protein:
        protein_instruction = f"CRITICAL: The main protein in the recipe MUST be {primary_protein} (e.g., use Chicken shanks, not Beef shanks). Do not substitute this primary protein."
    
    else:
         protein_instruction = "CRITICAL: Base the recipe on the main protein found in the Required Ingredients list."

    prompt = f"""
You are an expert Filipino home cook.
**Primary Goal:** Create a delicious version of "{recipe_name}" that **prominently features and is built around** the following ingredients: **{', '.join(required_ingredients)}**.
Dish: {recipe_name}
Required Ingredients: {', '.join(required_ingredients or [])}

Generate a recipe in the following **exact format**:

---
**TITLE RULE:** The main dish name MUST be exactly "{recipe_name}". You can add a descriptive subtitle inside the parentheses. For example: {recipe_name} (Filipino Style Omelette).
Dish Name (Filipino / English Description)
Servings: 1-2
Allergens: (List all common allergens like Shellfish, Peanuts, Gluten, Dairy, Eggs, or None)

Ingredients: 
**CRITICAL INSTRUCTION: The following ingredients MUST be included as primary, non-optional components of this recipe: {', '.join(required_ingredients or [])}. Do NOT list any of these under '(optional)'.**
List all ingredients with quantities. 
{protein_instruction} 
Include optional substitutions using "Sub:" 
Don't add texts like "-" 

Step-by-Step Cooking Instructions:

1. Step Title: 
  Detailed instruction(s). 
  Include cooking times, methods, and realistic household tips.

2. Step Title: 
  ...continue for all steps until the dish is ready.

🍲 Tips & Notes: 
Include optional tips for flavor, substitutions, serving suggestions, and dietary notes.
Don't add texts like "-" 

---

CRITICAL:
Include all required ingredients.
Use clear and concise language.
Maintain authentic Filipino household cooking methods.
Keep the recipe reader-friendly.
"""

    result = run_openai(prompt, model=model, max_tokens=2000)
    if use_cache:
        steps_cache[cache_key] = result

    return result

# MERGE NOTE: This function was identical in both versions.
def extract_recipe_names(recipes_text):
    """Extract recipe names from common formats:
    - "Recipe N: Name" (with description on following line)
    - "N. Name: Description" or "N) Name: Description"
    - "N. Name" (no description on same line)
    """
    if not recipes_text:
        return []

    names: list[str] = []

    # Pattern A: Recipe N: Name
    for m in re.findall(r"(?im)^\s*Recipe\s+\d+\s*:\s*(.+?)\s*$", recipes_text):
        name = m.strip()
        if name and name.lower() not in {n.lower() for n in names}:
            names.append(name)

    # Pattern B: N. Name[: description]
    for m in re.findall(r"(?im)^\s*\d+\s*[\.)]\s*([^\n]+)$", recipes_text):
        # Strip any trailing inline description after a colon
        name = m.split(":", 1)[0].strip()
        if name and name.lower() not in {n.lower() for n in names}:
            names.append(name)

    return names

# MERGE NOTE: This function was identical in both versions.
def clear_cache():
    recipe_cache.clear()
    steps_cache.clear()
    return {"message": "Cache cleared successfully"}

# MERGE NOTE: This function was identical in both versions.
def get_cache_stats():
    return {
        "recipe_cache_size": len(recipe_cache),
        "steps_cache_maxsize": steps_cache.maxsize,
        "recipe_cache_ttl": recipe_cache.ttl,
        "steps_cache_ttl": steps_cache.ttl,
        "note": "Caching is disabled by default - all searches return fresh results"
    }
