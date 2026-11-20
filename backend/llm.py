"""Minimal Groq client. Every caller must handle a None return (demo mode / API failure)."""
import json
import logging

import httpx

from backend.config import GROQ_API_KEY, GROQ_MODEL, GROQ_URL, LLM_ENABLED

log = logging.getLogger("prepwise.llm")


def complete(messages, *, as_json=False, temperature=0.3, max_tokens=1800):
    if not LLM_ENABLED:
        return None
    body = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if as_json:
        body["response_format"] = {"type": "json_object"}
    try:
        res = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json=body,
            timeout=60,
        )
        res.raise_for_status()
        text = res.json()["choices"][0]["message"]["content"]
    except Exception as exc:  # network, quota, bad key
        log.warning("LLM call failed: %s", exc)
        return None
    if not as_json:
        return text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        log.warning("LLM returned invalid JSON")
        return None
