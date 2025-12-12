#!/usr/bin/env python3
# /home/surecode/Documents/eatnearby/community/views/gemini_test.py*-
"""
Simple AI Chat using OpenRouter API
-----------------------------------
Uses requests to interact with an OpenAI-compatible model.
"""

import requests

# ================= CONFIGURATION ================= #
API_KEY = ""  # <-- put your OpenRouter API key here privately
MODEL = "openai/gpt-4.1-mini"  # Free/low-cost model
MAX_TOKENS = 200  # Safe for free-tier usage

# ================= FUNCTION ================= #
def ask_ai(prompt: str) -> str:
    """
    Send a prompt to the AI model and return its response.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raises error for bad status codes
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Error: {e}"

# ================= MAIN LOOP ================= #
if __name__ == "__main__":
    print("🤖 AI Chat (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break
        bot_reply = ask_ai(user_input)
        print("Bot:", bot_reply)
