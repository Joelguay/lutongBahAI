import sys
import argparse
import atexit
from ingredient_integration import run_yolo_detection, read_detected_ingredients, cleanup_captured_directory

def cleanup_on_exit():
    """Clean up captured directory when program exits"""
    cleanup_captured_directory()

def main():
    parser = argparse.ArgumentParser(description="Filipino Recipe Generator with YOLO Ingredient Detection")
    parser.add_argument("--api", action="store_true", help="Run as Flask API server")
    parser.add_argument("--no-detection", action="store_true", help="Skip YOLO detection, use default ingredients")
    parser.add_argument("--weights", type=str, help="Path to YOLO model weights (.pt file)")
    parser.add_argument("--source", type=str, default="0", help="Source for detection (webcam index, image path, etc.)")
    parser.add_argument("--conf", type=float, default=0.5, help="Confidence threshold for detection")
    parser.add_argument("--keep-captured", action="store_true", help="Keep captured directory after session (don't auto-cleanup)")
    
    args = parser.parse_args()
    
    # Register cleanup function to run on exit
    if not args.keep_captured:
        atexit.register(cleanup_on_exit)
    
    if args.api:
        # Run as Flask API
        from api import app
        print("Starting Flask API server...")
        print("Press Ctrl+C to stop server and cleanup captured directory")
        try:
            app.run(host="0.0.0.0", port=5000, debug=True)
        except KeyboardInterrupt:
            print("\nShutting down server...")
            if not args.keep_captured:
                cleanup_captured_directory()
    else:
        # Run as CLI with ingredient detection
        print("=== Filipino Recipe Generator with YOLO Detection ===\n")
        
        try:
            # Lazy import LLM utils so app can start before OPENAI_API_KEY is set
            from llm_utils import generate_recipes, extract_recipe_names, get_recipe_steps

            # Run YOLO detection first (unless explicitly skipped), then read detected ingredients
            use_detection = not args.no_detection
            if use_detection:
                run_yolo_detection(weights_path=args.weights, source=args.source, conf=args.conf)
                import time
                time.sleep(2)
                # Read ingredients and also prepare the raw detection JSON (latest file)
                ingredients = read_detected_ingredients()
                # Try to include raw JSON to help the LLM, but keep same output format
                detection_json_text = None
                try:
                    from ingredient_integration import get_latest_detection_file
                    latest_file = get_latest_detection_file()
                    if latest_file:
                        with open(latest_file, 'r') as f:
                            detection_json_text = f.read()
                except Exception:
                    detection_json_text = None
            else:
                ingredients = ["chicken", "banana", "potato"]
            
            print(f"\nUsing ingredients: {', '.join(ingredients)}")
            print("\nGenerating Filipino recipes...")
            
            # Generate recipes using detected ingredients (and raw JSON if available)
            recipes_text = generate_recipes(ingredients, detection_json_text=detection_json_text)
            if isinstance(recipes_text, str) and recipes_text.startswith("Error:"):
                print(recipes_text)
                sys.exit(1)
            print(recipes_text)

            # Extract recipe names
            recipe_names = extract_recipe_names(recipes_text)
            if not recipe_names:
                print(
                    "Could not extract recipe names automatically. Please rerun or check the output."
                )
                sys.exit(1)
            else:
                # Show numbered list
                print("\nPlease choose a recipe to see detailed steps:")
                for idx, name in enumerate(recipe_names, 1):
                    print(f"{idx}. {name}")
                while True:
                    try:
                        choice = int(input("Enter the number of your choice: "))
                        if 1 <= choice <= len(recipe_names):
                            chosen_recipe = recipe_names[choice - 1]
                            break
                        else:
                            print("Invalid choice. Try again.")
                    except ValueError:
                        print("Please enter a valid number.")

            print(f"\nDetailed Steps for '{chosen_recipe}':\n")
            steps_text = get_recipe_steps(chosen_recipe)
            if isinstance(steps_text, str) and steps_text.startswith("Error:"):
                print(steps_text)
                sys.exit(1)
            print(steps_text)
            
        except KeyboardInterrupt:
            print("\n\nSession interrupted by user.")
        except Exception as e:
            print(f"\nError during execution: {e}")
        finally:
            # Final cleanup if not keeping captured files
            if not args.keep_captured:
                cleanup_captured_directory()

if __name__ == "__main__":
    main()