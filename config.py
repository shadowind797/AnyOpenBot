import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
PROXY_URL: str = os.getenv("PROXY_URL", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-3.5-flash")
PUBLIC_URL: str = os.getenv("PUBLIC_URL", "")
