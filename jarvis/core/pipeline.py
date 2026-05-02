"""
core/pipeline.py

Responsibility: Orchestrate the full command-processing flow.

The pipeline is the ONLY module that knows about the order of operations.
Individual modules know nothing about each other -- the pipeline connects them.

Usage:
    from jarvis.core.pipeline import Pipeline

    pipeline = Pipeline()
    cmd = pipeline.process("i'm bored, play something fun")
    print(cmd.response)

Phase 3+ Architecture:
    AI path  (when GEMINI_API_KEY is set):
        raw -> [Input Handler] -> [Chat Logger] -> [AI Parser (Gemini)] -> [Executor]

    Fallback (when AI unavailable or fails):
        raw -> [Input Handler] -> [Preprocessor] -> [Intent Parser]
                              -> [Entity Extractor] -> [Executor]

    Style learning:
        After 20 messages, Gemini auto-extracts the user's typing style
        and stores it in memory.json. Future parses use it automatically.
"""

from jarvis.core.command import Command, INTENT_UNKNOWN
from jarvis.core import input_handler
from jarvis.core import preprocessor
from jarvis.core import intent_parser
from jarvis.core import entity_extractor
from jarvis.core import ai_parser          # Phase 3+
from jarvis.core import chat_logger        # Style learning
from jarvis.core import style_learner      # Style learning


class Pipeline:
    """
    Processes raw user input through the full command pipeline.

    Phase 3 Stages (AI path):
        1. Input Handler  -- normalize raw text
        2. AI Parser      -- LLM classifies intent + extracts entities in one call
        3. Action Executor -- perform the real-world action

    Phase 2 Fallback Stages (if AI unavailable):
        1. Input Handler
        2. Preprocessor
        3. Intent Parser
        4. Entity Extractor
        5. Action Executor
    """

    def __init__(self):
        self._executor = None
        self._recent_context: list[str] = []   # Rolling window of last 5 inputs

        # Check once at startup whether AI is available
        self._ai_available = ai_parser.is_available()
        if self._ai_available:
            print("  [AI] Groq parser active (llama-3.3-70b) + Gemini style learning")
            # Show style status
            total = chat_logger.get_total_count()
            if total >= chat_logger.STYLE_EXTRACTION_THRESHOLD:
                print(f"  [AI] Style profile active ({total} messages learned)")
            else:
                remaining = chat_logger.STYLE_EXTRACTION_THRESHOLD - total
                print(f"  [AI] Style learning: {total} messages logged ({remaining} more to unlock)")
        else:
            print("  [AI] No GROQ_API_KEY found. Using Phase 2 rule-based parser.")

    def set_executor(self, executor) -> None:
        """Inject the action executor."""
        self._executor = executor

    def _parse_with_ai(self, cmd: Command) -> tuple[Command, bool]:
        """
        Attempt AI parsing. Returns (cmd, success).
        Fills cmd.intent and cmd.entities if successful.
        Passes recent context so Gemini can resolve follow-up commands.
        """
        intent, entities = ai_parser.parse(
            cmd.clean_input,
            recent_context=self._recent_context
        )

        if intent == INTENT_UNKNOWN or not entities:
            # AI returned nothing useful -- trigger fallback
            return cmd, False

        cmd.intent   = intent
        cmd.entities = entities
        return cmd, True

    def _maybe_learn_style(self) -> None:
        """
        If we've crossed the style learning threshold and no profile
        exists yet, trigger Gemini to extract the user's style.
        Runs silently -- never blocks the main command loop.
        """
        try:
            from jarvis.core import memory
            existing = memory.get("style_profile")
            if existing:
                return  # Already learned -- skip
            if not chat_logger.is_ready_for_style_learning():
                return  # Not enough messages yet

            messages = chat_logger.get_recent(40)
            profile = style_learner.extract_style_profile(messages)
            if profile:
                memory.set("style_profile", profile)
                print("\n  [AI] Style profile updated! JARVIS now understands your way of typing.")
        except Exception:
            pass  # Never crash the pipeline over style learning

    def _parse_with_rules(self, cmd: Command) -> Command:
        """
        Phase 2 rule-based parsing pipeline (fallback).
        """
        # Preprocess
        cmd.clean_input = preprocessor.process(cmd.clean_input)

        if not cmd.clean_input:
            cmd.response = "I heard you, but what would you like me to do?"
            return cmd

        # Intent
        cmd.intent, matched_trigger = intent_parser.parse(cmd.clean_input)

        if cmd.intent == INTENT_UNKNOWN:
            cmd.response = (
                "I'm not sure what you mean. "
                "Try 'play <song>', 'open <app>', 'go to <site>', or 'search <query>'."
            )
            return cmd

        # Entities
        cmd.entities = entity_extractor.extract(
            cmd.intent, cmd.clean_input, matched_trigger
        )

        if not cmd.entities:
            cmd.response = (
                f"I understood you want to {cmd.intent.replace('_', ' ').lower()}, "
                f"but I couldn't figure out what. Could you be more specific?"
            )
            return cmd

        return cmd

    def process(self, raw_input: str) -> Command:
        """
        Run raw user input through the full pipeline.

        Args:
            raw_input: The exact string the user typed.

        Returns:
            A fully populated Command object.
        """
        # -- Stage 0: Create Command Object -----------------------------------
        cmd = Command(raw_input)

        # -- Stage 1: Normalize input -----------------------------------------
        cmd.clean_input = input_handler.handle(raw_input)

        if not cmd.clean_input:
            cmd.response = "I didn't catch that. Please type a command."
            return cmd

        # -- Stage 1b: Log the message for style learning ---------------------
        chat_logger.log(raw_input)

        # -- Stage 1c: Update rolling context window --------------------------
        self._recent_context.append(raw_input)
        if len(self._recent_context) > 5:
            self._recent_context.pop(0)

        # -- Stage 1d: Maybe trigger style learning (silent, non-blocking) ----
        if self._ai_available:
            self._maybe_learn_style()

        # -- Stage 2: Parse intent + entities ---------------------------------
        parsed = False

        if self._ai_available:
            cmd, parsed = self._parse_with_ai(cmd)

        if not parsed:
            # Either AI unavailable or AI returned UNKNOWN -- use rules
            cmd = self._parse_with_rules(cmd)
            # If rule parsing already set a response (guard fired), return
            if cmd.response:
                return cmd

        # -- Stage 3: Guard -- intent resolved but still no entities ----------
        if cmd.intent != INTENT_UNKNOWN and not cmd.entities:
            cmd.response = (
                f"I understood you want to {cmd.intent.replace('_', ' ').lower()}, "
                f"but I couldn't figure out what. Could you be more specific?"
            )
            return cmd

        # -- Stage 4: Execute action ------------------------------------------
        if self._executor:
            cmd = self._executor.execute(cmd)
        else:
            cmd.response = f"[Parsed OK] intent={cmd.intent}, entities={cmd.entities}"

        return cmd
