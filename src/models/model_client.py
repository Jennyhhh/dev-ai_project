
import os

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
).rstrip("/")

MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2")


def generate_response(
    prompt: str,
    system_prompt: str = "You are a helpful recipe assistant.",
    json_schema: dict | None = None,
    num_predict: int = 250,
) -> str:
    """Lähettää kehotteen paikalliselle Ollama-mallille.

    If json_schema is given, Ollama forces the answer to follow that JSON structure.
    """

    if not prompt or not prompt.strip():
        raise ValueError("Prompt ei saa olla tyhjä.")

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": num_predict,
        },
    }

    if json_schema is not None:
        payload["format"] = json_schema

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=120,
    )

    response.raise_for_status()
    data = response.json()
    content = data.get("message", {}).get("content", "")

    if not content:
        raise RuntimeError("Ollama ei palauttanut vastaustekstiä.")

    return content.strip()