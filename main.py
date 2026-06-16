from chat import SYSTEM_PROMPT, get_reply
from voice import listen

def main():
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    print("\n=========================")
    print("        LIQ ASSISTANT")
    print("=========================")
    print("1. Type")
    print("2. Voice")
    print("3. Exit\n")

    while True:
        try:
            choice = input("Choose (1/2/3): ").strip()

            if choice == "1":
                user_input = input("You: ").strip()

                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("Goodbye.")
                    break

                if not user_input:
                    continue

                try:
                    print("\nLiq is thinking...\n")
                    reply = get_reply(messages, user_input)
                    print(f"Liq: {reply}\n")
                except Exception as e:
                    print(f"\nLiq Error: {e}")
                    print("Please make sure Ollama is running.\n")

            elif choice == "2":
                try:
                    user_input = listen()

                    if not user_input:
                        print("I could not hear anything clearly.\n")
                        continue

                    print(f"\nYou: {user_input}\n")

                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("Goodbye.")
                        break

                    print("Liq is thinking...\n")
                    reply = get_reply(messages, user_input)
                    print(f"Liq: {reply}\n")

                except Exception as e:
                    print(f"\nVoice Error: {e}\n")

            elif choice == "3":
                print("Goodbye.")
                break

            else:
                print("Please choose 1, 2, or 3.\n")

        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
        except EOFError:
            print("\nGoodbye.")
            break

if __name__ == "__main__":
    main()