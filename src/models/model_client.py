
import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
).rstrip("/")

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "llama3.2",
)

DEFAULT_TIMEOUT = 180


def generate_response(
    prompt: str,
    system_prompt: str = "You are a helpful recipe assistant.",
    json_schema: dict | None = None,
    num_predict: int = 800,
) -> str:
    """
    Generates a response using the local Ollama model.

    Supports:
    - Normal chatbot responses
    - Structured JSON responses
    - Configurable response length
    - Clear connection and timeout errors
    """

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("The prompt cannot be empty.")

    if not isinstance(system_prompt, str):
        raise ValueError("The system prompt must be a string.")

    if num_predict <= 0:
        raise ValueError("num_predict must be greater than zero.")

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt.strip(),
            },
        ],
        "stream": False,
        "options": {
            "temperature": (
                0.1 if json_schema is not None else 0.3
            ),
            "num_predict": num_predict,
        },
    }

    if json_schema is not None:
        payload["format"] = json_schema

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )

        response.raise_for_status()

    except requests.exceptions.ConnectionError as error:
        logger.error("Cannot connect to Ollama: %s", error)

        raise RuntimeError(
            "Cannot connect to Ollama. "
            "Make sure Ollama is running on your computer."
        ) from error

    except requests.exceptions.Timeout as error:
        logger.error("Ollama request timed out: %s", error)

        raise RuntimeError(
            "Ollama took too long to respond. "
            "Please try again."
        ) from error

    except requests.exceptions.HTTPError as error:
        logger.error("Ollama HTTP error: %s", error)

        status_code = response.status_code

        if status_code == 404:
            raise RuntimeError(
                f"Ollama model '{MODEL_NAME}' was not found. "
                f"Run: ollama pull {MODEL_NAME}"
            ) from error

        raise RuntimeError(
            f"Ollama returned an HTTP error: {status_code}"
        ) from error

    except requests.exceptions.RequestException as error:
        logger.error("Ollama request failed: %s", error)

        raise RuntimeError(
            "An error occurred while communicating with Ollama."
        ) from error

    try:
        data = response.json()

    except ValueError as error:
        logger.error("Invalid Ollama JSON response: %s", error)

        raise RuntimeError(
            "Ollama returned an invalid response."
        ) from error

    message = data.get("message")

    if not isinstance(message, dict):
        raise RuntimeError(
            "Ollama returned an unexpected message format."
        )

    content = message.get("content", "")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "Ollama did not return a text response."
        )

    if data.get("done_reason") == "length":
        logger.warning(
            "Ollama response may have been truncated."
        )

        if json_schema is not None:
            raise RuntimeError(
                "Ollama stopped before completing the JSON response."
            )

    return content.strip()
