import os
import sys
import json
import logging
from datetime import datetime
import google.generativeai as genai
from django.conf import settings
logger = logging.getLogger(__name__)


API_KEYS = settings.GEMINI_KEYS



API_STATE_FILE = "api_state.json"
CHAT_HISTORY_FILE = "chat_history.json"


def load_api_state():
    try:
        if os.path.exists(API_STATE_FILE):
            with open(API_STATE_FILE, "r") as f:
                state = json.load(f)
                if (
                    isinstance(state, dict)
                    and "current_key_index" in state
                    and "usage_count" in state
                ):
                    return state
    except Exception:
        pass
    return {"current_key_index": 0, "usage_count": 0}


def save_api_state(state):
    try:
        with open(API_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save API state: {e}")


def get_next_api_key():
    state = load_api_state()
    current_index = state["current_key_index"]
    usage_count = state["usage_count"] + 1

    if usage_count >= 50 or current_index >= len(API_KEYS):
        next_index = (current_index + 1) % len(API_KEYS)
        usage_count = 1
        logger.warning(f"Rotating API key: {current_index} -> {next_index}")
    else:
        next_index = current_index

    new_state = {"current_key_index": next_index, "usage_count": usage_count}
    save_api_state(new_state)

    return API_KEYS[next_index]


def load_chat_history():
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_chat_history(history):
    try:
        with open(CHAT_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save chat history: {e}")


def build_context_prompt(history, new_prompt):
    if not history:
        return new_prompt

    context = "Previous conversation:\n"
    for msg in history:
        role = "User" if msg["type"] == "user" else "Assistant"
        context += f"{role}: {msg['content']}\n"
    context += f"\nUser: {new_prompt}\nAssistant:"
    return context


def get_gemini_response(user_prompt: str) -> str:
    history = load_chat_history()
    context_prompt = build_context_prompt(history, user_prompt)

    api_key = get_next_api_key()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    try:
        response = model.generate_content(context_prompt)

        history.append({"type": "user", "content": user_prompt, "time": datetime.now().isoformat()})
        history.append({"type": "assistant", "content": response.text, "time": datetime.now().isoformat()})

        if len(history) > 20:
            history = history[-20:]

        save_chat_history(history)

        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}", exc_info=True)
        return "Sorry, I had trouble processing your request. Please try again."
