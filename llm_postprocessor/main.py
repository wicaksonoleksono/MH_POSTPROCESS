"""Entry point for LLM post-processor."""

import argparse
import json
from pathlib import Path

from llm_postprocessor import PostProcessor
from llm_postprocessor.config import get_settings
from llm_postprocessor.io.json_reader import JsonReader
from llm_postprocessor.utils.helpers import get_all_json_files, ensure_dir


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LLM Post-processor")
    parser.add_argument(
        "--input", type=str, help="Input JSON file or directory"
    )
    parser.add_argument(
        "--output", type=str, help="Output directory"
    )
    parser.add_argument(
        "--config", type=str, help="Configuration file"
    )

    args = parser.parse_args()

    # Get settings
    settings = get_settings()
    if args.output:
        settings.processor.output_dir = args.output

    # Initialize processor
    processor = PostProcessor(settings)

    # Process input
    if args.input:
        input_path = Path(args.input)
        if input_path.is_file():
            # Process single file
            session_data = JsonReader.read_session_data(input_path)
            result = processor.process_session(session_data)
            print(result.model_dump_json(indent=2))
        elif input_path.is_dir():
            # Process directory
            json_files = get_all_json_files(input_path)
            print(f"Found {len(json_files)} JSON files")
            # TODO: Process batch
    else:
        print("Please provide --input parameter")


if __name__ == "__main__":
    main()
