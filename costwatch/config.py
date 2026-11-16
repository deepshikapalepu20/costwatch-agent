
import os
from dotenv import load_dotenv

load_dotenv()

AWS_PROFILE   = os.getenv("AWS_PROFILE", "").strip()
AWS_REGION    = os.getenv("AWS_REGION", "us-east-1")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL    = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "21600"))
BASELINE_USD  = float(os.getenv("BASELINE_DAILY_USD", "1.00"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "7"))
SIMULATE      = os.getenv("SIMULATE_ANOMALY", "false").lower() == "true"
REPORT_DIR    = os.getenv("REPORT_DIR", "reports")
