#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API Chat Tool
--------------------
Updated version with better error handling and response validation.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
import google.generativeai as genai


# ========= CONFIGURATION ========= #
API_KEYS = [
    # Replace these with your actual API keys or use environment variables
    os.getenv("GEMINI_KEY_1", "AIzaSyAHFqqjfPBh-OQcKl22Froced5khhgUivQ"),
    os.getenv("GEMINI_KEY_2", "AIzaSyAW0hNz5fVDORqfL21BLw8PSwDdqUesLP8"),
    os.getenv("GEMINI_KEY_3", "AIzaSyDsDJnTy7ZWGaCtLd84mt6b4mDu4tfNr34"),
]

API_STATE_FILE = "api_state.json"
CHAT_HISTORY_FILE = "chat_history.json"
LOG_FILE = "gemini_log.txt"

MAX_HISTORY = 20
ROTATION_LIMIT = 50
RETRY_LIMIT = 3


# ========= LOGGING ========= #
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


# ========= API STATE MANAGEMENT ========= #
def load_api_state():
    if os.path.exists(API_STATE_FILE):
        try:
            with open(API_STATE_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            logging.warning(f"Failed to load API state: {e}")
    return {"current_key_index": 0, "usage_count": 0}


def save_api_state(state):
    try:
        with open(API_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save API state: {e}")


def rotate_api_key():
    """Rotate to the next API key"""
    state = load_api_state()
    next_index = (state.get("current_key_index", 0) + 1) % len(API_KEYS)
    state.update({"current_key_index": next_index, "usage_count": 0})
    save_api_state(state)
    logging.info(f"🔁 Rotated API key → Index {next_index}")
    return API_KEYS[next_index]


def get_current_api_key():
    """Retrieve API key with usage tracking and rotation"""
    state = load_api_state()
    index = state.get("current_key_index", 0)
    usage = state.get("usage_count", 0) + 1

    if usage >= ROTATION_LIMIT:
        return rotate_api_key()

    state.update({"usage_count": usage})
    save_api_state(state)

    return API_KEYS[index % len(API_KEYS)]


# ========= CHAT HISTORY ========= #
def load_chat_history():
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logging.warning(f"Error loading chat history: {e}")
    return []


def save_chat_history(history):
    try:
        with open(CHAT_HISTORY_FILE, "w") as f:
            json.dump(history[-MAX_HISTORY:], f, indent=2)
    except Exception as e:
        logging.error(f"Error saving chat history: {e}")


def build_context_prompt(history, prompt):
    """Combine previous messages into context"""
    if not history:
        return prompt
    
    context = "Previous conversation:\n"
    for msg in history[-5:]:
        context += f"{msg['type'].capitalize()}: {msg['content']}\n"
    context += f"\nUser: {prompt}\nAssistant:"
    return context


# ========= GEMINI QUERY ========= #
def query_gemini(prompt):
    """Send a prompt to Gemini, handle retries & key rotation"""
    for attempt in range(RETRY_LIMIT):
        api_key = get_current_api_key()
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")  # Changed to experimental model
            
            # Configure safety settings to be less restrictive
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
            ]
            
            # Add generation config
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            response = model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config=generation_config
            )
            
            # Check if response was blocked
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason
                logging.warning(f"Response blocked: {block_reason}")
                raise Exception(f"Response blocked: {block_reason}")
            
            # Validate response
            if not response.text:
                logging.warning("Empty response received")
                if attempt < RETRY_LIMIT - 1:
                    time.sleep(1)
                    continue
                else:
                    return "I apologize, but I couldn't generate a response. This might be due to content safety filters or a temporary issue."
            
            return response.text

        except Exception as e:
            err = str(e).lower()
            logging.error(f"Gemini API error (attempt {attempt + 1}): {e}")

            if any(k in err for k in ["quota", "403", "429", "invalid", "limit", "api key", "block"]):
                logging.warning("⚠️ API key issue detected — rotating key")
                rotate_api_key()
                time.sleep(2)
            else:
                if attempt < RETRY_LIMIT - 1:
                    logging.info(f"Retrying... (attempt {attempt + 2})")
                    time.sleep(1)
                else:
                    logging.error(f"Final error after {RETRY_LIMIT} attempts: {e}")
                    return f"Error: {str(e)}"


# ========= MAIN APP ========= #
def main():
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        user_input = input("💬 Ask Gemini: ").strip()

    if not user_input:
        print("❌ Please provide a question.")
        return

    history = load_chat_history()
    
    # Use simpler prompt for first message, context for subsequent ones
    if len(history) > 0:
        prompt = build_context_prompt(history, user_input)
    else:
        prompt = user_input

    print("⏳ Processing your request...")
    
    try:
        answer = query_gemini(prompt)

        # Add to history
        history.append({"type": "user", "content": user_input, "time": datetime.now().isoformat()})
        history.append({"type": "assistant", "content": answer, "time": datetime.now().isoformat()})
        save_chat_history(history)

        print(f"\n🤖 Gemini:\n{answer}\n")

    except Exception as e:
        logging.error(f"❌ Final error: {e}")
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()