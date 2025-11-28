#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# community/views/gemini_test.py

"""
Test ONLY Gemini models that may work for free accounts.
"""

import os
import google.generativeai as genai

API_KEY = os.getenv("GEMINI_KEY_1", "AIzaSyCKqIBWGpTGX4yY5JU6JSKwwjYj05au6SQ")

# Expanded list of FREE Gemini models to test
FREE_MODELS = [
    # Gemini 2.0 Models (Newest - Most Likely to Work)
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-thinking-exp",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-preview",
    
    # Gemini 1.5 Models (Good Balance)
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-latest",
    
    # Gemini 1.0 Models (Older but Stable)
    "gemini-1.0-pro",
    "gemini-1.0-pro-001",
    "gemini-1.0-pro-latest",
    
    # Experimental & Flash Variants
    "gemini-pro",
    "gemini-flash",
    "models/gemini-pro",
    "models/gemini-flash",
    
    # Specific Model IDs
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-exp",
    "models/gemini-2.0-flash-thinking-exp", 
    "models/gemini-2.0-flash-lite",
    "models/gemini-2.0-flash-lite-preview",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-flash-8b",
    "models/gemini-1.5-flash-001",
    "models/gemini-1.0-pro",
    "models/gemini-1.0-pro-001",
]

PROMPT = "Say one short sentence so I can confirm you're working."

def test_models():
    genai.configure(api_key=API_KEY)
    working_models = []
    
    print(f"🧪 Testing {len(FREE_MODELS)} free Gemini models...\n")
    
    for model_name in FREE_MODELS:
        print(f"🔹 Testing: {model_name}")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(PROMPT)

            if hasattr(response, "text") and response.text:
                print(f"✅ WORKING - Response: {response.text}")
                working_models.append({
                    'name': model_name,
                    'response': response.text,
                    'status': 'WORKING'
                })
            else:
                print(f"❌ No text returned")
                
        except Exception as e:
            error_str = str(e)
            if "quota" in error_str.lower():
                print(f"🚫 QUOTA EXCEEDED")
            elif "not found" in error_str.lower():
                print(f"📛 MODEL NOT FOUND")
            elif "permission" in error_str.lower():
                print(f"🔒 PERMISSION DENIED")
            elif "location" in error_str.lower():
                print(f"🌍 LOCATION RESTRICTED")
            else:
                print(f"❌ Error: {error_str[:80]}...")

    # Display results
    print(f"\n{'='*50}")
    print(f"🎯 TEST RESULTS:")
    print(f"{'='*50}")
    
    if working_models:
        print(f"✅ {len(working_models)} WORKING MODELS FOUND:")
        for model in working_models:
            print(f"   🟢 {model['name']}")
            print(f"      📝 Response: {model['response']}")
    else:
        print(f"❌ NO WORKING MODELS FOUND")
        print(f"💡 Possible issues:")
        print(f"   • API key has no quota")
        print(f"   • Regional restrictions")
        print(f"   • Account not activated")
    
    return working_models

def get_fastest_model(working_models):
    """Test speed of working models"""
    if not working_models:
        return None
        
    print(f"\n⚡ SPEED TESTING WORKING MODELS...")
    
    speed_results = []
    for model_info in working_models:
        model_name = model_info['name']
        try:
            import time
            model = genai.GenerativeModel(model_name)
            
            # Test speed with 3 requests
            times = []
            for i in range(3):
                start_time = time.time()
                response = model.generate_content("Say 'speed test' quickly.")
                end_time = time.time()
                if response.text:
                    times.append(end_time - start_time)
            
            if times:
                avg_time = sum(times) / len(times)
                speed_results.append({
                    'name': model_name,
                    'avg_time': avg_time,
                    'status': 'SPEED_TESTED'
                })
                print(f"   ⚡ {model_name}: {avg_time:.3f}s avg")
                
        except Exception as e:
            print(f"   ❌ Speed test failed for {model_name}: {e}")
    
    # Return fastest model
    if speed_results:
        fastest = min(speed_results, key=lambda x: x['avg_time'])
        print(f"\n🚀 FASTEST MODEL: {fastest['name']} ({fastest['avg_time']:.3f}s)")
        return fastest['name']
    
    return working_models[0]['name'] if working_models else None

if __name__ == "__main__":
    working = test_models()
    fastest = get_fastest_model(working)
    
    if fastest:
        print(f"\n🎊 RECOMMENDED MODEL FOR YOUR APP: {fastest}")
        print(f"\n💡 Add this to your gemini_client.py:")
        print(f'   model = genai.GenerativeModel("{fastest}")')
    else:
        print(f"\n💡 No working models found. Check your API key and account status.")