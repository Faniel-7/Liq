import ollama

MODEL = "llama3.2:3b"

SYSTEM_PROMPT = """
You are Liq, a helpful local AI assistant built by Faniel Negasi.
Facts:
- Faniel Negasi is your creator.
- Faniel Negasi is male.
- When referring to Faniel Negasi, use male pronouns (he, him, his).

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
        try:
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

            print("\nLiq is thinking...\n")

            try:
                response = ollama.chat(
                    model=MODEL,
                    messages=messages
                )

                assistant_reply = response["message"]["content"]
                print(f"Liq: {assistant_reply}\n")

                messages.append({
                    "role": "assistant",
                    "content": assistant_reply
                })

            except Exception as e:
                print(f"\nLiq Error: {e}")
                print("Please make sure Ollama is running.\n")

        except KeyboardInterrupt:
            print("\nGoodbye.")
            break

        except EOFError:
            print("\nGoodbye.")
            break

if __name__ == "__main__":
    chat()