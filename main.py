import ollama

MODEL = "llama3.2:3b"

def chat():
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        }
    ]

    print("Llama 3.2:3B assistant started.")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye.")
            break

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        response = ollama.chat(
            model=MODEL,
            messages=messages
        )

        assistant_reply = response["message"]["content"]
        print(f"\nAssistant: {assistant_reply}\n")

        messages.append({"role": "assistant", "content": assistant_reply})

if __name__ == "__main__":
    chat()