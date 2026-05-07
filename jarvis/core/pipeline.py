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
from jarvis.core import chat_responder     # Phase 8: conversational chat mode
from jarvis.core import chat_memory_extractor  # Phase 8: smart chat memory
from jarvis.core import memory             # Phase 8: user name for personalization


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
        self._recent_context: list[str] = []   # Rolling window: "You: ...", "JARVIS: ..."

        # Check once at startup whether AI is available
        self._ai_available = ai_parser.is_available()
        self._chat_available = chat_responder.is_available()
        if self._ai_available:
            print("  [AI] Groq parser active (llama-3.3-70b) + Gemini style learning")
            if self._chat_available:
                print("  [AI] Conversational chat mode: active (witty + warm)")
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

        When this method cannot determine an intent, it returns the command
        with INTENT_UNKNOWN and NO response set, so the caller (process())
        can route the input to the LLM chat responder instead of showing
        a canned error.
        """
        # Preprocess
        preprocessed = preprocessor.process(cmd.clean_input)

        if not preprocessed:
            # Preprocessor stripped everything (e.g. just "hi" or "hello").
            # Leave intent as UNKNOWN with no response — caller will route
            # to LLM chat responder.
            return cmd

        # Intent
        cmd.intent, matched_trigger = intent_parser.parse(preprocessed)

        if cmd.intent == INTENT_UNKNOWN:
            # Rules couldn't classify — leave response empty so the caller
            # routes to LLM chat responder.
            return cmd

        # Update clean_input with the preprocessed version for entity extraction
        cmd.clean_input = preprocessed

        # Entities
        cmd.entities = entity_extractor.extract(
            cmd.intent, cmd.clean_input, matched_trigger
        )

        if not cmd.entities:
            cmd.response = f"I understood you want to {cmd.intent.replace('_', ' ').lower()}, but I couldn't figure out what. Could you be more specific?"
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

        # -- Stage 1c: Maybe trigger style learning (silent, non-blocking) ----
        if self._ai_available:
            self._maybe_learn_style()

        # -- Stage 2: Parse intent + entities ---------------------------------
        parsed = False
        ai_response = ""
        actions = []

        if self._ai_available:
            actions, ai_response, emotion = ai_parser.parse(
                cmd.clean_input, self._recent_context
            )
            if actions or ai_response:
                parsed = True

        # -- Fast Path for AI-parsed input (single or multiple actions) -------
        if parsed:
            cmd.success = True
            cmd.mode = "chat"
            cmd.response = ai_response if ai_response else "Done."

            execution_errors = []

            for action in actions:
                intent = action.get("intent", "CHAT")
                if intent == "CHAT" or intent == "INTENT_UNKNOWN":
                    continue
                
                # Execute each action using a temporary Command object
                temp_cmd = Command(raw_input)
                temp_cmd.intent = intent
                
                # Map entities
                target = action.get("target")
                value = action.get("value")
                query = action.get("search_query")
                
                if intent == "SYSTEM_CONTROL":
                    temp_cmd.entities = {"action": target, "value": str(value) if value is not None else ""}
                elif intent == "PLAY_MEDIA":
                    temp_cmd.entities = {"song_name": query if query else target}
                elif intent == "OPEN_APP":
                    temp_cmd.entities = {"app_name": target}
                elif intent == "OPEN_WEBSITE":
                    temp_cmd.entities = {"website": target}
                else:
                    temp_cmd.entities = {}
                    if target: temp_cmd.entities["target"] = target
                    if value: temp_cmd.entities["value"] = str(value)
                    if query: temp_cmd.entities["query"] = query

                if self._executor:
                    result_cmd = self._executor.execute(temp_cmd)
                    if not result_cmd.success:
                        execution_errors.append(f"Could not {intent}: {result_cmd.response}")

            # Append any execution errors to the AI's natural response so the user knows
            if execution_errors:
                cmd.response += "\n\nHowever, I ran into some issues: " + ", ".join(execution_errors)

            # Silently extract any important personal info in the background
            chat_memory_extractor.extract_async(cmd.raw_input)

            # Store this turn in context before returning
            self._recent_context.append(f"You: {raw_input}")
            self._recent_context.append(f"JARVIS: {cmd.response}")
            self._recent_context = self._recent_context[-10:]  # Keep last 5 turns
            return cmd

        # -- Fallback path: AI parser failed or unavailable -------------------
        # Try rule-based parser as fallback
        cmd = self._parse_with_rules(cmd)

        if cmd.intent == INTENT_UNKNOWN:
            # Both AI and rules couldn't classify this — it's conversational chat.
            # Use the LLM chat responder to generate a real reply instead of
            # a canned error message.
            user_name = memory.get_user_name()
            cmd.response = chat_responder.reply(
                cmd.raw_input,
                recent_context=self._recent_context,
                user_name=user_name,
            )
            cmd.success = True
            cmd.mode    = "chat"

            chat_memory_extractor.extract_async(cmd.raw_input)

            self._recent_context.append(f"You: {raw_input}")
            self._recent_context.append(f"JARVIS: {cmd.response}")
            self._recent_context = self._recent_context[-10:]  # Keep last 5 turns
            return cmd

        # -- Fallback Stage 3: Guard -- intent resolved but still no entities --
        if cmd.intent != INTENT_UNKNOWN and not cmd.entities:
            user_name = memory.get_user_name()
            if self._chat_available:
                cmd.response = chat_responder.reply(
                    cmd.raw_input,
                    recent_context=self._recent_context,
                    user_name=user_name,
                    action_result=f"I understood the intent ({cmd.intent}) but couldn't determine what specifically to act on.",
                )
            else:
                cmd.response = (
                    f"I understood you want to {cmd.intent.replace('_', ' ').lower()}, "
                    f"but I couldn't figure out what. Could you be more specific?"
                )
            cmd.success = True
            cmd.mode = "chat"
            self._recent_context.append(f"You: {raw_input}")
            self._recent_context.append(f"JARVIS: {cmd.response}")
            self._recent_context = self._recent_context[-10:]
            return cmd

        # -- Fallback Stage 4: Execute action ---------------------------------
        if self._executor:
            cmd = self._executor.execute(cmd)
        else:
            cmd.response = f"[Parsed OK] intent={cmd.intent}, entities={cmd.entities}"

        # -- Fallback Stage 5: Make the response conversational ---------------
        executor_response = cmd.response
        if self._chat_available:
            user_name = memory.get_user_name()
            cmd.response = chat_responder.reply(
                cmd.raw_input,
                recent_context=self._recent_context,
                user_name=user_name,
                action_result=executor_response,
            )
        cmd.mode = "chat"

        # -- Fallback Stage 6: Update rolling conversation context ------------
        self._recent_context.append(f"You: {raw_input}")
        self._recent_context.append(f"JARVIS: {cmd.response}")
        self._recent_context = self._recent_context[-10:]  # Keep last 5 turns

        return cmd

