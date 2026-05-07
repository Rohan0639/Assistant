"""
core/groq_client.py

Manages Groq API clients, supporting multiple API keys to automatically
bypass rate limits.

If GROQ_API_KEYS is defined as a comma-separated list in .env, it will rotate
through them when a rate limit is hit.
"""

import os
import logging
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
logger = logging.getLogger(__name__)

_clients: list[Groq] = []
_current_idx = 0


def _init_clients() -> None:
    global _clients
    if _clients:
        return

    keys_str = os.getenv("GROQ_API_KEYS", "")
    keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    
    if not keys:
        single_key = os.getenv("GROQ_API_KEY", "")
        if single_key.strip():
            keys = [single_key.strip()]
            
    if not keys:
        return
        
    _clients = [Groq(api_key=k) for k in keys]
    logger.info("Initialized Groq client manager with %d keys.", len(_clients))


def is_available() -> bool:
    """Return True if at least one Groq API key is configured."""
    _init_clients()
    return len(_clients) > 0


def get_completion(model: str, messages: list[dict], temperature: float = 0.1, max_tokens: int = 150):
    """
    Wrapper for Groq chat completions that automatically rotates API keys
    if a rate limit (429) is hit.
    """
    global _clients, _current_idx
    _init_clients()
    
    if not _clients:
        raise ValueError("No Groq API keys configured.")
        
    attempts = len(_clients)
    last_err = None
    
    for _ in range(attempts):
        client = _clients[_current_idx]
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response
        except Exception as e:
            err_str = str(e).lower()
            if "rate limit" in err_str or "429" in err_str:
                logger.warning("Groq rate limit hit on key #%d, switching to next key...", _current_idx + 1)
                _current_idx = (_current_idx + 1) % len(_clients)
                last_err = e
            else:
                # If it's a different error, raise it immediately
                raise e
                
    # If we exhausted all keys and still failed due to rate limits
    raise Exception(f"All {attempts} Groq API keys are currently rate-limited. Last error: {last_err}")
