#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Free Model Test
---------------------
Simple script to check which Gemini models work with your API key.
Automatically stops after finding the first working model.
"""

import os
import google.generativeai as genai

# ================= CONFIGURATION ================= #
# Set your API key here or via environment variable
API_KEY = os.getenv("GEMINI_KEY_1", "AIzaSyC3z1QK44KpUe4S3bPFzicty8sK5LWxGvk")

# Models to test
MODELS = [
    "models/gemini-1.5-flash",    # Free tier
    "models/gemini-2.0-flash",    # Experimental / may require quota
    "models/gemini-2.0-flash-exp" # Experimental / limited
]

# Test prompt
PROMPT = "Explain how AI works in a few words."

# ================= MAIN FUNCTION ================= #
def test_models():
    genai.configure(api_key=API_KEY)

    for model_name in MODELS:
        print(f"🔹 Testing model: {model_name}")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(PROMPT)

            # Extract text safely
            text_output = None
            if hasattr(response, "text") and response.text:
                text_output = response.text
            elif hasattr(response, "candidates") and response.candidates:
                try:
                    text_output = response.candidates[0].content.parts[0].text
                except Exception:
                    text_output = str(response.candidates[0])

            if text_output:
                print(f"✅ Response: {text_output}\n")
                print(f"🎯 Working model: {model_name}")
                break  # Stop after first successful model
            else:
                print(f"⚠️ No text returned for {model_name}\n")

        except Exception as e:
            print(f"❌ Error for {model_name}: {e}\n")

# ================= ENTRY POINT ================= #
if __name__ == "__main__":
    test_models()
