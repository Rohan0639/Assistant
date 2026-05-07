"""
core/chat_responder.py

Conversational AI responder for JARVIS — handles inputs that aren't system
commands (classified UNKNOWN by the AI parser).

Personality: Witty like Tony Stark's JARVIS + Warm like a trusted friend.
  - Clever, slightly sarcastic — but never rude
  - Genuinely helpful, encouraging
  - Suggests JARVIS actions when contextually relevant
  - Always replies in English (even if user writes Hinglish)
  - Maintains multi-turn conversation context

Uses Groq (llama-3.3-70b-versatile) — same API key as ai_parser.py.
"""

import os
import logging

from dotenv import load_dotenv
from jarvis.core import groq_client

load_dotenv()
logger = logging.getLogger(__name__)

# ── Groq client configuration ─────────────────────────────────────────────────

def is_available() -> bool:
    """Return True if the chat responder is configured and ready."""
    return groq_client.is_available()


# ── Personality system prompt ─────────────────────────────────────────────────

_SYSTEM_PROMPT_TEMPLATE = """
You are {agent_name} — a personal AI assistant with the sharp wit of Tony Stark's JARVIS
and the warmth of a genuinely caring friend.

Your identity (NEVER deviate from this):
  - Your name is {agent_name}. When asked "what is your name?" or "who are you?",
    always answer "{agent_name}" — no exceptions, no hedging.
  - You are NOT ChatGPT, Gemini, or any other AI. You are {agent_name}.
  - You were built to be a personal assistant for the user.

Your personality:
  - Witty, clever, and lightly sarcastic — but never mean or condescending
  - Warm and encouraging — you actually want the user to succeed
  - Concise — every sentence earns its place. No padding, no filler
  - Always reply in English, regardless of what language the user uses

Your action capabilities (suggest naturally when relevant, never force it):
  - Open desktop apps: Chrome, VS Code, Notepad, Spotify, etc.
  - Play music on YouTube
  - Open any website
  - Search the web
  - Control system volume, mute, sleep, lock screen, shutdown, restart
  - Open folders: Downloads, Desktop, Documents, Pictures, etc.
  - Check system info: battery, RAM, CPU, disk space
  - Run system commands: ipconfig, task manager, disk cleanup, etc.
  - Remember things you tell it (names, preferences)
  - Run multi-step workflows: morning routine, coding session, chill mode, etc.

When to naturally suggest an action (only when it fits the moment):
  - User sounds bored → suggest music or YouTube
  - User mentions working/coding → offer to open VS Code or run a workflow
  - User sounds stressed → suggest calming music or a break
  - User asks about system health → offer to run a check
  - Keep suggestions brief — one sentence at most, at the end of your reply

Conversation rules:
  1. Keep replies short: 2–4 sentences for simple questions; longer only if truly needed
  2. No bullet points unless the user asks for a list
  3. Don't echo or restate the user's question
  4. Never say "As an AI language model..." — you are {agent_name}
  5. If you genuinely don't know something, say so briefly and offer to help another way
  6. Use the user's name naturally — maybe once per message, not every sentence
  7. Treat the user like an intelligent adult. No baby talk.
""".strip()


def _build_system_prompt(agent_name: str, user_name: str) -> str:
    """Build the personalized system prompt with agent and user names."""
    prompt = _SYSTEM_PROMPT_TEMPLATE.format(agent_name=agent_name)
    if user_name:
        prompt += f"\n\nThe user's name is {user_name}. Address them naturally — not every sentence."
    return prompt


# ── Main reply function ───────────────────────────────────────────────────────

def reply(
    user_input: str,
    recent_context: list[str] | None = None,
    user_name: str = "",
    action_result: str = "",
) -> str:
    """
    Generate a conversational reply to the user's input.

    Args:
        user_input:     The user's message.
        recent_context: Rolling window of recent conversation turns.
                        Format: ["You: <msg>", "JARVIS: <reply>", ...]
        user_name:      The user's stored name, for personalization.
        action_result:  Optional. If provided, describes an action that was
                        just executed (e.g. "Opened Chrome successfully").
                        The LLM will incorporate this into a natural reply.

    Returns:
        A warm, human-like reply string.
    """
    if not is_available():
        return (
            "I'd love to chat, but my conversational engine isn't ready yet. "
            "Make sure GROQ_API_KEY is set in your .env file."
        )

    # Load agent name from memory (defaults to JARVIS)
    try:
        from jarvis.core import memory as _mem
        agent_name = _mem.get("agent_name", "JARVIS") or "JARVIS"
        if not user_name:
            user_name = _mem.get_user_name()
    except Exception:
        agent_name = "JARVIS"

    system = _build_system_prompt(agent_name=agent_name, user_name=user_name)

    # If an action was executed, tell the LLM what happened so it can
    # respond naturally about it (e.g. "Done! Chrome is up and running.")
    if action_result:
        system += (
            "\n\n--- ACTION JUST PERFORMED ---\n"
            f"You just executed an action for the user. Result: {action_result}\n"
            "Respond conversationally about what you did. Be natural and brief — "
            "don't just parrot the result. You can add a short follow-up suggestion "
            "if relevant. Keep it to 1-2 sentences."
        )

    # Build message history from recent context
    messages: list[dict] = [{"role": "system", "content": system}]

    if recent_context:
        for turn in recent_context[-8:]:   # Last 4 full turns (8 lines)
            if turn.startswith("You: "):
                messages.append({"role": "user", "content": turn[5:]})
            elif turn.startswith(f"{agent_name}: "):
                messages.append({"role": "assistant", "content": turn[len(agent_name)+2:]})
            elif turn.startswith("JARVIS: "):  # backward compat
                messages.append({"role": "assistant", "content": turn[8:]})

    # Append the current user message
    messages.append({"role": "user", "content": user_input})

    try:
        response = groq_client.get_completion(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.85,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error("Chat responder error: %s", e)
        # If we had an action result, at least return that
        if action_result:
            return action_result
        return "My thoughts got tangled up there. Give me a moment and try again."

