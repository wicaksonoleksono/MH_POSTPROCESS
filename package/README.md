# LLM Post-processor

A Python package for post-processing data with LLMs using LangChain and Pydantic for structured I/O.

## Features

- Pydantic-based schema validation for input/output
- Conversation formatting utilities for quick previews
- Lightweight summaries for PHQ / LLM assessment JSONL files
- Automatic copying of raw PHQ/LLM artifacts (analysis JSONL, responses, metadata) into processed folders
- Batch processing support via simple CLI entry points

## Installation

```bash
pip install -e .
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```python
from llm_postprocessor import PostProcessor
from llm_postprocessor.schemas.input_schemas import SessionData, UserMetadata

# Initialize processor
processor = PostProcessor()

# Create session data
user = UserMetadata(user_id="user_123", session_id="session_456")
session = SessionData(user=user, llm_conversation=[], metadata={})

# Process session (produces formatted conversation + assessment summaries)
result = processor.process_session(session)
print(result)
```

### Configuration

Set environment variables for configuration:

```bash
# Optional package settings
export PROCESSOR_INPUT_DIR=./data
export PROCESSOR_OUTPUT_DIR=./output
```

Or create `.env` file:

```
# Package settings
PROCESSOR_OUTPUT_DIR=./output
```

### Command Line

```bash
python main.py --input data/session.json --output ./results
```

## Project Structure

```
llm_postprocessor/
├── schemas/              # Pydantic models
│   ├── input_schemas.py
│   └── output_schemas.py
├── llm/                  # LLM clients and prompts
│   ├── client.py
│   └── prompts.py
├── postprocessor/        # Core processing logic
│   ├── processor.py
│   └── chains.py
├── io/                   # JSON I/O
│   ├── json_reader.py
│   └── json_writer.py
├── utils/                # Helper functions
│   └── helpers.py
├── config.py            # Configuration management
└── __init__.py
```

## Dependencies

- `pydantic>=2.0`
- `langchain>=0.1.0`
- `langchain-openai>=0.0.1`
- `langchain-community>=0.0.1`

## Development

To contribute or modify:

1. Install in editable mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Format code:
   ```bash
   black llm_postprocessor
   isort llm_postprocessor
   ```

3. Lint:
   ```bash
   flake8 llm_postprocessor
   mypy llm_postprocessor
   ```

## License

MIT
