from chat import SYSTEM_PROMPT, get_reply
from voice import listen
from speak import speak

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
    print("1. Type mode")
    print("2. Voice mode")
    print("3. Exit\n")

    while True:
        try:
            choice = input("Choose (1/2/3): ").strip()

            if choice == "1":
                while True:
                    user_input = input("You: ").strip()

                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("Goodbye.")
                        return

                    if not user_input:
                        continue

                    try:
                        print("\nLiq is thinking...\n")
                        reply = get_reply(messages, user_input)
                        print(f"Liq: {reply}\n")
                        speak(reply)
                    except Exception as e:
                        print(f"\nLiq Error: {e}\n")

            elif choice == "2":
                print("\nVoice mode started.")
                print("Say 'exit', 'quit', or 'bye' to stop.\n")

                while True:
                    try:
                        user_input = listen()

                        if not user_input:
                            print("I could not hear anything clearly.\n")
                            continue

                        print(f"\nYou: {user_input}\n")

                        if user_input.lower() in ["exit", "quit", "bye"]:
                            print("Goodbye.")
                            return

                        print("Liq is thinking...\n")
                        reply = get_reply(messages, user_input)
                        print(f"Liq: {reply}\n")
                        speak(reply)

                    except Exception as e:
                        print(f"\nVoice Error: {e}\n")

            elif choice == "3":
                print("Goodbye.")
                return

            else:
                print("Please choose 1, 2, or 3.\n")

        except KeyboardInterrupt:
            print("\nGoodbye.")
            return
        except EOFError:
            print("\nGoodbye.")
            return

if __name__ == "__main__":
    main()