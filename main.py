import ollama

MODEL = "llama3.2:3b"

SYSTEM_PROMPT = """
You are Liq, a helpful local AI assistant built by Faniel Negasi.

Your role:
- Help with coding and technology questions.
- Be concise and accurate.
- Give step-by-step instructions when appropriate.
- Remember the current conversation context.
- Be friendly and professional.

Never claim to be ChatGPT.
Always introduce yourself as Liq if asked who you are.
"""

def chat():
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    print("Liq assistant started.")
    print("Type 'exit', 'quit', or 'bye' to stop.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye.")
            break

        if not user_input:
            continue

        messages.append({
            "role": "user",
            "content": user_input
        })

        response = ollama.chat(
            model=MODEL,
            messages=messages
        )

        assistant_reply = response["message"]["content"]
        print(f"\nLiq: {assistant_reply}\n")

        messages.append({
            "role": "assistant",
            "content": assistant_reply
        })

if __name__ == "__main__":
    chat()