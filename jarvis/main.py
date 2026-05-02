"""
main.py

Entry point for JARVIS.

Starts an interactive command loop that:
    1. Accepts user text input
    2. Processes it through the full pipeline
    3. Prints the assistant's response
    4. Loops until the user types 'exit' or 'quit'

Run with:
    python jarvis/main.py
"""

import sys
import os

# Force UTF-8 output on Windows terminals
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Ensure project root (parent of jarvis/) is on the path when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jarvis.core.pipeline import Pipeline
from jarvis.actions.executor import ActionExecutor
from jarvis.core import memory                  # Phase 5


# -- Banner -------------------------------------------------------------------

BANNER = """
+------------------------------------------------------+
|                                                      |
|        J.A.R.V.I.S  -- Personal AI Assistant        |
|        Just A Rather Very Intelligent System        |
|                                                      |
|   Try:                                               |
|     play <song>           -> opens YouTube          |
|     open <app>            -> launches a desktop app |
|     go to <site>          -> opens a website        |
|     search <query>        -> Google search          |
|     my name is <name>     -> remembers your name    |
|     start coding session  -> multi-step workflow    |
|     what do you know?     -> recalls your prefs     |
|     exit / quit           -> shut down              |
|                                                      |
+------------------------------------------------------+
"""

EXIT_COMMANDS = {"exit", "quit", "q", "bye", "shutdown"}


def _personalized_greeting() -> str:
    """Return a greeting using stored name if available."""
    name = memory.get_user_name()
    last = memory.get("last_seen")

    if name and last:
        return f"  Welcome back, {name}! (Last seen: {last})"
    elif name:
        return f"  Hello, {name}! Good to see you."
    else:
        return "  Ready. Tell me your name to get started! (e.g. 'my name is Rohan')"


def build_pipeline() -> Pipeline:
    """Initialize and return a ready-to-use pipeline with executor attached."""
    pipeline = Pipeline()
    pipeline.set_executor(ActionExecutor())
    return pipeline


def format_response(cmd) -> str:
    """Format the assistant's response for display."""
    prefix = "[OK] JARVIS:" if cmd.success else "[!] JARVIS:"
    return f"\n  {prefix} {cmd.response}\n"


def run():
    """Main input loop."""
    print(BANNER)

    pipeline = build_pipeline()

    # Phase 5: personalized greeting + update last_seen
    print(_personalized_greeting())
    memory.update_last_seen()
    print()

    while True:
        try:
            # Prompt -- show name if known
            name = memory.get_user_name()
            prompt = f"  {name}: " if name else "  You: "
            raw = input(prompt).strip()

            # Exit check
            if raw.lower() in EXIT_COMMANDS:
                name = memory.get_user_name()
                farewell = f"Goodbye, {name}!" if name else "Goodbye."
                print(f"\n  JARVIS: {farewell}\n")
                break

            # Skip blank lines silently
            if not raw:
                continue

            # Process through pipeline
            cmd = pipeline.process(raw)

            # Display response
            print(format_response(cmd))

        except KeyboardInterrupt:
            print("\n\n  JARVIS: Shutting down. Goodbye.\n")
            break


if __name__ == "__main__":
    run()
