# LLM Post-processor

A Python package for post-processing data with LLMs using LangChain and Pydantic for structured I/O.

## Features

- Pydantic-based schema validation for input/output
- Support for multiple LLM providers (OpenAI, TogetherAI)
- LangChain integration for chaining operations
- JSON reader/writer utilities
- Batch processing support
- Type-safe configuration management

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
session = SessionData(user=user, phq_responses={}, llm_conversation=[])

# Process session
result = processor.process_session(session)
print(result)
```

### Configuration

Set environment variables for configuration:

```bash
# API keys are automatically read by LangChain from these env vars:
export OPENAI_API_KEY=sk-...        # For OpenAI
export TOGETHER_API_KEY=...          # For TogetherAI

# Package settings
export LLM_PROVIDER=openai
export LLM_MODEL_NAME=gpt-3.5-turbo
export LLM_TEMPERATURE=0.7
export PROCESSOR_INPUT_DIR=./data
export PROCESSOR_OUTPUT_DIR=./output
```

Or create `.env` file:

```
# API keys (LangChain reads these automatically)
OPENAI_API_KEY=sk-...
TOGETHER_API_KEY=...

# Package settings
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-3.5-turbo
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
