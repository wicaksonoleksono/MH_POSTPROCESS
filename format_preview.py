"""Preview conversation formatting without full package import."""
import json
from pathlib import Path
def load_conversation(file_path):
    """Load conversation from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conversations = data.get("conversations", [])
    messages = []

    for turn in conversations:
        # User message first
        user_msg = turn.get("user_message")
        if user_msg:
            messages.append({"role": "user", "content": user_msg})
        ai_msg = turn.get("ai_message")
        if ai_msg:
            messages.append({"role": "ai", "content": ai_msg})

    return messages


def format_messages(messages, include_metadata=False):
    """Format messages to mahasiswa/sindi format."""
    role_map = {"user": "mahasiswa", "ai": "sindi"}
    formatted_lines = []

    for turn, msg in enumerate(messages, 1):
        role = msg.get("role", "")
        content = msg.get("content", "").strip()

        if role and content:
            formatted_role = role_map.get(role, role)
            if include_metadata:
                formatted_lines.append(f"[Turn {turn}] {formatted_role}: {content}")
            else:
                formatted_lines.append(f"{formatted_role}: {content}")

    return "\n".join(formatted_lines)


def get_stats(messages):
    """Get conversation statistics."""
    if not messages:
        return {"total": 0, "mahasiswa": 0, "sindi": 0, "avg_length": 0.0}

    role_counts = {"user": 0, "ai": 0}
    total_chars = 0

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role in role_counts:
            role_counts[role] += 1
        total_chars += len(content)

    total = len(messages)
    avg_length = total_chars / total if total > 0 else 0

    return {
        "total": total,
        "mahasiswa": role_counts["user"],
        "sindi": role_counts["ai"],
        "avg_length": round(avg_length, 2),
        "total_chars": total_chars,
    }


if __name__ == "__main__":
    conv_file = "data/user_11_miko_session1/llm_conversation.json"

    print("=" * 80)
    print("CONVERSATION FORMATTING PREVIEW")
    print("=" * 80)

    # Load messages
    messages = load_conversation(conv_file)
    stats = get_stats(messages)

    # Show statistics
    print(f"\n📊 STATISTICS:")
    print(f"  Total messages: {stats['total']}")
    print(f"  Mahasiswa (user): {stats['mahasiswa']}")
    print(f"  Sindi (AI): {stats['sindi']}")
    print(f"  Avg message length: {stats['avg_length']} chars")
    print(f"  Total chars: {stats['total_chars']}")

    # Show formatted output
    print(f"\n📝 FORMATTED OUTPUT (plain):")
    print("-" * 80)
    formatted = format_messages(messages, include_metadata=False)
    print(formatted)

    # Show formatted with metadata
    print(f"\n📝 FORMATTED OUTPUT (with turn numbers):")
    print("-" * 80)
    formatted_meta = format_messages(messages, include_metadata=True)
    print(formatted_meta[:1500])
    print("... (truncated)")

    print("\n" + "=" * 80)
    print("✓ Formatting preview complete!")
    print("=" * 80)
