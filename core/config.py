import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

# --- Load environment variables ---
load_dotenv()

# --- Azure OpenAI Settings ---
API_KEY        = os.getenv("API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
API_VERSION    = os.getenv("API_VERSION")
MODEL          = os.getenv("MODEL")

# --- Browser Display Settings ---
DISPLAY_WIDTH  = int(os.getenv("DISPLAY_WIDTH", 1920))
DISPLAY_HEIGHT = int(os.getenv("DISPLAY_HEIGHT", 1200))

# --- Iteration Settings ---
ITERATIONS = int(os.getenv("ITERATIONS", 9))

# --- Screenshot Save Path ---
SCREENSHOT_ROOT = Path(__file__).resolve().parent.parent / os.getenv("SCREENSHOT_DIR", "screenshots")

# --- Azure OpenAI Client Instance ---
client = AzureOpenAI(
    api_key=API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    api_version=API_VERSION
)
