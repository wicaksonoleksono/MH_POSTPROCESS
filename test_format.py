"""Test conversation formatting."""

from package.llm_postprocessor.io.json_reader import JsonReader
from package.llm_postprocessor.io.conversation_loader import ChatHistoryFormatter
import json

if __name__ == "__main__":
    # Test with sample file
    conv_file = "data/user_11_miko_session1/llm_conversation.json"

    print("=" * 80)
    print("CONVERSATION FORMATTING TEST")
    print("=" * 80)

    # Load raw messages
    print("\n1. RAW MESSAGES (as structured list):")
    print("-" * 80)
    messages = JsonReader.read_conversation(conv_file)
    print(json.dumps(messages[:2], indent=2, ensure_ascii=False))
    print(f"... ({len(messages)} total messages)")

    # Format as mahasiswa/sindi
    print("\n2. FORMATTED FOR LLM PROMPTS (mahasiswa/sindi format):")
    print("-" * 80)
    formatted = ChatHistoryFormatter.format_from_file(conv_file)
    print(formatted)

    print("\n" + "=" * 80)
    print(f"Total messages: {len(messages)}")
    print(f"Formatted length: {len(formatted)} characters")
    print("=" * 80)
