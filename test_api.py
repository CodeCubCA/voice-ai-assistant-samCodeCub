import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {api_key[:10]}..." if api_key else "No API key found")

genai.configure(api_key=api_key)

# Test the API
try:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content("Say hello!")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
