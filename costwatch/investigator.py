import logging
import requests
import json
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
def run(payload):
    """
    Investigate incoming Alertmanager alerts.
    """
    alerts = payload.get("alerts", [])

    if not alerts:
        log.warning("No alerts received for investigation.")
        return

    for index, alert in enumerate(alerts, start=1):
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})

        prompt = f"""
        You are a cloud infrastructure cost investigation agent.

        Investigate the following alert:

        Alert labels:
        {json.dumps(labels, indent=2)}

        Alert annotations:
        {json.dumps(annotations, indent=2)}

        Analyze the alert and provide:

        1. Possible root cause.
        2. Potential cloud cost impact.
        3. Recommended investigation steps.
        4. Suggested cost optimization actions.
        5. Risks associated with the recommendations.

        Clearly distinguish confirmed evidence from assumptions.
        """

        log.info("Starting investigation for alert %d", index)

        result = ask(prompt)

        log.info(
            "Investigation completed for alert %d:\n%s",
            index,
            result
        )
