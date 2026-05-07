"""
actions/media.py

Handles PLAY_MEDIA intent.

Phase 1 strategy:
    Open a YouTube search for the song name in the default browser.
    No Spotify API, no authentication, no external dependencies.

Phase 3 upgrade path:
    Replace the webbrowser call with a Spotify/YouTube API call.
    The interface (play_media(song_name) → (bool, str)) stays identical.
"""

import webbrowser
from urllib.parse import quote_plus


def play_media(song_name: str) -> tuple[bool, str]:
    """
    Play a song by automatically navigating to the first YouTube result.

    Args:
        song_name: The name of the song extracted from user input.

    Returns:
        (success, response_message)
    """
    if not song_name:
        return False, "What song would you like me to play?"

    # DuckDuckGo's "I'm Feeling Lucky" syntax (!ducky) automatically
    # redirects to the first search result. We scope it to YouTube.
    encoded = quote_plus(f"!ducky site:youtube.com {song_name}")
    url = f"https://duckduckgo.com/?q={encoded}"
    webbrowser.open(url)
    
    return True, f"Playing '{song_name}' on YouTube..."
