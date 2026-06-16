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

def get_reply(messages, user_input):
    messages.append({
        "role": "user",
        "content": user_input
    })

    response = ollama.chat(
        model=MODEL,
        messages=messages
    )

    assistant_reply = response["message"]["content"]

    messages.append({
        "role": "assistant",
        "content": assistant_reply
    })

    return assistant_reply