import sys
import time
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="AI Episode Parser Process")
    parser.add_argument("--temp-dir", dest="temp_dir", required=True, help="Path to temp directory for downloading models")
    parser.add_argument("--simulate-error", dest="simulate_error", action="store_true", help="Simulate a parser error")
    args = parser.parse_args()

    temp_dir = args.temp_dir
    os.makedirs(temp_dir, exist_ok=True)

    if args.simulate_error:
        sys.stderr.write("Error: Failed to connect to AI model repository.\n")
        sys.stderr.flush()
        sys.exit(1)

    steps = 20
    for i in range(1, steps + 1):
        time.sleep(0.08)
        progress = (i / steps) * 100.0
        sys.stdout.write(f"PROGRESS:{progress:.1f}\n")
        sys.stdout.flush()

    model_file = os.path.join(temp_dir, "kyaa_ai_model.bin")
    with open(model_file, "w", encoding="utf-8") as f:
        f.write("KYAA_AI_EPISODE_PARSER_MODEL_V1")

    sys.stdout.write(f"MODEL_SAVED:{model_file}\n")
    sys.stdout.flush()
    sys.exit(0)

if __name__ == "__main__":
    main()
