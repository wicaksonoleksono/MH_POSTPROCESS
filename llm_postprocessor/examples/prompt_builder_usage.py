"""Example of using PromptBuilder for LLM analysis."""

from llm_postprocessor.llm.prompt_builder import PromptBuilder
from llm_postprocessor.llm.client import OpenAIClient


def main():
    """Demonstrate prompt builder usage."""

    # Sample chat history
    chat_history = [
        {
            "role": "Sindi",
            "content": "Hai, apa kabar? Kamu terlihat lelah akhir-akhir ini."
        },
        {
            "role": "Teman",
            "content": "Iya, aku memang merasa lelah banget. Rasanya nggak ada energi buat apa-apa."
        },
        {
            "role": "Sindi",
            "content": "Sudah berapa lama kamu merasa seperti ini?"
        },
        {
            "role": "Teman",
            "content": "Mungkin sekitar 2 minggu terakhir. Aku juga susah tidur, dan kalau tidur pun rasanya nggak puas."
        },
    ]

    # Initialize builder
    builder = PromptBuilder()

    # Build messages
    messages = builder.build_analysis_messages(chat_history)

    print("=== Generated Message Chain ===\n")
    for i, msg in enumerate(messages, 1):
        print(f"Message {i} ({msg.__class__.__name__}):")
        print(msg.content)
        print("\n" + "="*50 + "\n")

    # Optional: Use with LLM client
    print("\n=== Using with LLM Client ===\n")
    try:
        # Initialize LLM client (requires OPENAI_API_KEY env var)
        llm_client = OpenAIClient(model_name="gpt-3.5-turbo")
        llm = llm_client.get_client()

        # Invoke with messages
        # response = llm.invoke(messages)
        # print("LLM Response:", response.content)

        print("LLM client initialized successfully!")
        print("Uncomment the invoke lines to get actual LLM response.")
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        print("Make sure OPENAI_API_KEY is set in environment.")


if __name__ == "__main__":
    main()
