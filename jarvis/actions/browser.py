"""
actions/browser.py

Handles all browser-based actions:
    - OPEN_WEBSITE: Navigate to a known or unknown website
    - SEARCH_WEB:   Open a Google search in the browser

Uses Python's built-in `webbrowser` module — no external dependencies.
"""

import webbrowser
from urllib.parse import quote_plus

from jarvis.config.apps import WEBSITE_REGISTRY


def open_website(website: str) -> tuple[bool, str]:
    """
    Open a website in the default browser.

    First checks WEBSITE_REGISTRY for known shorthand names.
    Falls back to treating the input as a raw URL if not recognized.

    Args:
        website: What the user said (e.g. "youtube", "github.com")

    Returns:
        (success, response_message)
    """
    # Check registry first (handles "youtube" → "https://www.youtube.com")
    url = WEBSITE_REGISTRY.get(website.lower())

    if not url:
        # Not a known shortcut — try as a direct URL
        if "." in website:
            url = f"https://{website}" if not website.startswith("http") else website
        else:
            return False, (
                f"I don't know the website '{website}'. "
                f"Try something like 'go to youtube' or 'visit github.com'."
            )

    webbrowser.open(url)
    return True, f"Opening {website} in your browser..."


def search_web(query: str) -> tuple[bool, str]:
    """
    Open a Google search for the given query.

    Args:
        query: The search query string.

    Returns:
        (success, response_message)
    """
    if not query:
        return False, "What would you like me to search for?"

    encoded = quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    return True, f"Searching Google for '{query}'..."
