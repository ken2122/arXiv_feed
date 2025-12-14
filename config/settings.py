import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_URL = os.getenv("CHAT_URL")
CHAT_TOKEN = os.getenv("CHAT_TOKEN")
CHAT_USER_ID = os.getenv("CHAT_USER_ID")
ROOM_ID = os.getenv("ROOM_ID")