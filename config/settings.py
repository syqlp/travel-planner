"""
配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
    VERBOSE = os.getenv("VERBOSE", "True").lower() == "true"

settings = Settings()