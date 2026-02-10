import os
from dotenv import find_dotenv, load_dotenv

print(f"Searching for .env file...")
env_path = find_dotenv()
if env_path:
    print(f"Found .env at: {env_path}")
    load_dotenv(env_path)
else:
    print("No .env file found by python-dotenv.")

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    masked = f"{api_key[:5]}...{api_key[-5:]}"
    print(f"OPENAI_API_KEY is SET: {masked}")
else:
    print("OPENAI_API_KEY is NOT SET in this environment.")
