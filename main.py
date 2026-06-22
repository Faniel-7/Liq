from chat import SYSTEM_PROMPT, get_reply
from voice import listen
from speak import speak
from app_control import open_app, CURRENT_OS_LABEL
from system_info import handle_system_question
from calculator import calculate
from media_control import handle_music_command, run_music_command, get_available_players

def handle_local_command(user_input: str):
    text = user_input.strip().lower()

    if (
        "open vscode" in text
        or "open vs code" in text
        or "launch vscode" in text
        or "launch vs code" in text
    ):
        return open_app("vscode")

    if "open browser" in text or "launch browser" in text:
        return open_app("browser")

    if (
        "open file manager" in text
        or "open files" in text
        or "launch file manager" in text
    ):
        return open_app("file manager")

    if "open terminal" in text or "launch terminal" in text:
        return open_app("terminal")

    if "open telegram" in text or "launch telegram" in text or text == "telegram":
        return open_app("telegram")

    return None

def process_music_command(user_input: str):
    music_result = handle_music_command(user_input)

    if music_result is None:
        return False

    if music_result["needs_player"]:
        players = music_result["available_players"]

        if players:
            print("\nWhich player should I use?")
            for i, player in enumerate(players, start=1):
                print(f"{i}. {player}")
            print()

            choice = input("Choose a player name or number: ").strip().lower()

            if choice in ["back", "cancel", "exit", "quit", "bye"]:
                return True

            selected_player = None

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(players):
                    selected_player = players[index]
            else:
                selected_player = choice

            if not selected_player:
                print("\nLiq: I could not understand the player choice.\n")
                return True

            success, message = run_music_command("play-pause", selected_player)
        else:
            print("\nLiq: I could not find any active players right now.\n")
            return True

    else:
        success, message = run_music_command(
            music_result["action"],
            music_result["player"]
        )

    print(f"\nLiq: {message}\n")
    speak(message)
    return True

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
    print(f"Current OS: {CURRENT_OS_LABEL}")
    print()
    print("1. Type mode")
    print("2. Manual voice mode")
    print("3. Exit\n")

    while True:
        try:
            choice = input("Choose (1/2/3): ").strip()

            if choice == "1":
                print("\nType mode started.")
                print("Type 'back' to return to the menu.")
                print("Type 'exit', 'quit', or 'bye' to stop Liq.\n")

                while True:
                    user_input = input("You: ").strip()

                    if user_input.lower() == "back":
                        print()
                        break

                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("Goodbye.")
                        return

                    if not user_input:
                        continue

                   
                    if process_music_command(user_input):
                        continue

                    
                    local_result = handle_local_command(user_input)
                    if local_result is not None:
                        success, message = local_result
                        print(f"\nLiq: {message}\n")
                        speak(message)
                        continue

                    calc_reply = calculate(user_input)
                    if calc_reply:
                        print(f"\nLiq: {calc_reply}\n")
                        speak(calc_reply)
                        continue

                    
                    system_reply = handle_system_question(user_input)
                    if system_reply:
                        print(f"\nLiq: {system_reply}\n")
                        speak(system_reply)
                        continue

                    try:
                        print("\nLiq is thinking...\n")
                        reply = get_reply(messages, user_input)
                        print(f"Liq: {reply}\n")
                        speak(reply)
                    except Exception as e:
                        print(f"\nLiq Error: {e}\n")

            elif choice == "2":
                print("\nManual voice mode started.")
                print("Press Enter to start recording.")
                print("Press Enter again to stop recording.")
                print("Type 'exit', 'quit', or 'bye' at the start prompt to stop.\n")

                while True:
                    start = input("Press Enter to start recording...").strip()

                    if start.lower() in ["exit", "quit", "bye"]:
                        print("Goodbye.")
                        return

                    user_input = listen()

                    if not user_input:
                        print("I could not hear anything clearly.\n")
                        continue

                    print(f"\nYou: {user_input}\n")

                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("Goodbye.")
                        return

            
                    if process_music_command(user_input):
                        continue

                  
                    local_result = handle_local_command(user_input)
                    if local_result is not None:
                        success, message = local_result
                        print(f"\nLiq: {message}\n")
                        speak(message)
                        continue

                 
                    calc_reply = calculate(user_input)
                    if calc_reply:
                        print(f"\nLiq: {calc_reply}\n")
                        speak(calc_reply)
                        continue

                   
                    system_reply = handle_system_question(user_input)
                    if system_reply:
                        print(f"\nLiq: {system_reply}\n")
                        speak(system_reply)
                        continue

                    try:
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