import sys
from llm_utils import run_openai, generate_recipes, extract_recipe_names

def main():
    print("== OpenAI Connectivity Test ==")
    pong = run_openai("Reply only with OK", model="gpt-4.1", max_tokens=2)
    print("Ping response:", pong)

    print("\n== Recipe Generation Test ==")
    txt = generate_recipes(["chicken", "garlic", "ginger"], use_cache=False, model="gpt-4.1")
    print("Raw output:\n" + str(txt))
    names = extract_recipe_names(txt)
    print("\nExtracted names:", names)
    if not names:
        sys.exit(2)

if __name__ == "__main__":
    main()

