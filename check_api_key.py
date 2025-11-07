import os

api_key = os.getenv('GEMINI_API_KEY')

if api_key:
    print("✅ GEMINI_API_KEY is accessible in PyCharm.")
    print(f"First 5 characters of the API key: {api_key[:5]}*****")
else:
    print("❌ GEMINI_API_KEY is NOT accessible in PyCharm.")
    print("Please ensure you have set the environment variable correctly and restarted PyCharm.")