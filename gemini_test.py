# import os
# import sys
# import json
# import google.generativeai as genai
# from datetime import datetime

# # List of API keys for rotation
# API_KEYS = [
#     "AIzaSyAHFqqjfPBh-OQcKl22Froced5khhgUivQ",
#     "AIzaSyAW0hNz5fVDORqfL21BLw8PSwDdqUesLP8",
#     "AIzaSyDsDJnTy7ZWGaCtLd84mt6b4mDu4tfNr34"
# ]

# # File to store current API key index and usage
# API_STATE_FILE = "api_state.json"

# # File to store chat history
# CHAT_HISTORY_FILE = "chat_history.json"

# def load_api_state():
#     """Load API key state from file"""
#     try:
#         if os.path.exists(API_STATE_FILE):
#             with open(API_STATE_FILE, 'r') as f:
#                 state = json.load(f)
#                 # Validate the state
#                 if (isinstance(state, dict) and 
#                     'current_key_index' in state and 
#                     'usage_count' in state and
#                     0 <= state['current_key_index'] < len(API_KEYS)):
#                     return state
#     except:
#         pass
#     # Default state if file doesn't exist or is invalid
#     return {'current_key_index': 0, 'usage_count': 0}

# def save_api_state(state):
#     """Save API key state to file"""
#     try:
#         with open(API_STATE_FILE, 'w') as f:
#             json.dump(state, f, indent=2)
#     except:
#         pass

# def get_next_api_key():
#     """Get the next available API key with rotation"""
#     state = load_api_state()
#     current_index = state['current_key_index']
#     usage_count = state['usage_count'] + 1
    
#     # Rotate key after 50 uses or if current index is invalid
#     if usage_count >= 50 or current_index >= len(API_KEYS):
#         next_index = (current_index + 1) % len(API_KEYS)
#         usage_count = 1  # Reset counter for new key
#         print(f"Rotating API key: {current_index} -> {next_index}", file=sys.stderr)
#     else:
#         next_index = current_index
    
#     # Update state
#     new_state = {
#         'current_key_index': next_index,
#         'usage_count': usage_count
#     }
#     save_api_state(new_state)
    
#     return API_KEYS[next_index]

# def load_chat_history():
#     """Load chat history from file"""
#     try:
#         if os.path.exists(CHAT_HISTORY_FILE):
#             with open(CHAT_HISTORY_FILE, 'r') as f:
#                 return json.load(f)
#     except:
#         pass
#     return []

# def save_chat_history(history):
#     """Save chat history to file"""
#     try:
#         with open(CHAT_HISTORY_FILE, 'w') as f:
#             json.dump(history, f, indent=2)
#     except:
#         pass

# def build_context_prompt(history, new_prompt):
#     """Build a prompt that includes conversation history"""
#     if not history:
#         return new_prompt
    
#     context = "Previous conversation:\n"
#     for msg in history:
#         if msg['type'] == 'user':
#             context += f"User: {msg['content']}\n"
#         else:
#             context += f"Assistant: {msg['content']}\n"
    
#     context += f"\nCurrent user message: {new_prompt}\n\nAssistant response:"
#     return context

# def main():
#     # Get prompt from command line arguments
#     if len(sys.argv) > 1:
#         user_prompt = " ".join(sys.argv[1:])
#     else:
#         user_prompt = "Tell me about Zambia"
    
#     # Load chat history
#     chat_history = load_chat_history()
    
#     # Build context-aware prompt
#     context_prompt = build_context_prompt(chat_history, user_prompt)
    
#     # Get API key with rotation
#     api_key = get_next_api_key()
    
#     try:
#         # Configure Gemini with current API key
#         genai.configure(api_key=api_key)
#         model = genai.GenerativeModel("gemini-1.5-flash")
        
#         # Generate response
#         response = model.generate_content(context_prompt)
        
#         # Add to chat history
#         chat_history.append({
#             'type': 'user',
#             'content': user_prompt,
#             'time': datetime.now().isoformat()
#         })
        
#         chat_history.append({
#             'type': 'assistant',
#             'content': response.text,
#             'time': datetime.now().isoformat()
#         })
        
#         # Keep only last 20 messages
#         if len(chat_history) > 20:
#             chat_history = chat_history[-20:]
        
#         # Save updated history
#         save_chat_history(chat_history)
        
#         # Print the response
#         print(response.text)
        
#     except Exception as e:
#         error_msg = str(e).lower()
        
#         # Check if it's an API key related error
#         if any(keyword in error_msg for keyword in ['quota', 'limit', 'exceeded', '403', '429', 'invalid', 'api', 'key']):
#             print(f"API key error detected: {e}", file=sys.stderr)
#             print("Rotating to next API key and retrying...", file=sys.stderr)
            
#             # Force rotate to next key
#             state = load_api_state()
#             next_index = (state['current_key_index'] + 1) % len(API_KEYS)
#             new_state = {
#                 'current_key_index': next_index,
#                 'usage_count': 1
#             }
#             save_api_state(new_state)
            
#             # Retry with new key
#             api_key = API_KEYS[next_index]
#             try:
#                 genai.configure(api_key=api_key)
#                 model = genai.GenerativeModel("gemini-1.5-flash")
#                 response = model.generate_content(context_prompt)
                
#                 # Update chat history with successful response
#                 chat_history.append({
#                     'type': 'user',
#                     'content': user_prompt,
#                     'time': datetime.now().isoformat()
#                 })
                
#                 chat_history.append({
#                     'type': 'assistant',
#                     'content': response.text,
#                     'time': datetime.now().isoformat()
#                 })
                
#                 if len(chat_history) > 20:
#                     chat_history = chat_history[-20:]
                
#                 save_chat_history(chat_history)
#                 print(response.text)
                
#             except Exception as retry_error:
#                 print(f"Error after API key rotation: {retry_error}", file=sys.stderr)
#                 sys.exit(1)
#         else:
#             # Other errors (not API key related)
#             print(f"Error: {e}", file=sys.stderr)
#             sys.exit(1)

# if __name__ == "__main__":
#     main()
    
import google.generativeai as genai

genai.configure(api_key="AIzaSyAW0hNz5fVDORqfL21BLw8PSwDdqUesLP8")

model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content("Explain why Zambia is famous for Victoria Falls.")
print(response.text)
