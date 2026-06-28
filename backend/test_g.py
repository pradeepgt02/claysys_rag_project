import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv(Path(__file__).parent / ".env", override=True)

key = os.getenv("GEMINI_API_KEY")
print("Key prefix:", key[:10] if key else "NOT FOUND")

genai.configure(api_key=key)

model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content("Reply with only: API key working")
print(response.text)