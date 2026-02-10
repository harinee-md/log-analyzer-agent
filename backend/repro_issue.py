import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

try:
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key present: {bool(api_key)}")
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key,
        temperature=0.1
    )
    print("ChatOpenAI initialized successfully")
except Exception as e:
    print(f"Error initializing ChatOpenAI: {e}")
