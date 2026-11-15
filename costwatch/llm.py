import logging
import requests
from . import config
 
log = logging.getLogger("costwatch.llm")
 
 
def _groq(prompt):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        json={
            "model": config.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
 
 
def _ollama(prompt):
    r = requests.post(
        f"{config.OLLAMA_URL}/api/generate",
        json={
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        },
        timeout=180,
    )
    r.raise_for_status()
    return r.json()["response"]
 
 
def ask(prompt):
    if config.GROQ_API_KEY:
        try:
            return _groq(prompt)
        except Exception as exc:
            log.warning("Groq failed (%s); falling back to Ollama", exc)
    try:
        return _ollama(prompt)
    except Exception as exc:
        log.error("Ollama failed: %s", exc)
        return "LLM unavailable. See the raw data section below for manual review."
