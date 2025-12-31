import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
TEMPERATURE = 0.0

if not API_KEY:
    raise ValueError("API Key not found. Please create a .env file.")

# Configure Gemini once here
genai.configure(api_key=API_KEY)