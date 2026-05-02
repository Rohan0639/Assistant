"""
actions/executor.py

Responsibility: Receive a Command object and dispatch to the correct handler.

The Executor is the ONLY module that knows about all action handlers.
Individual handlers (browser.py, apps.py, media.py) know nothing about
each other or the Command object.

Design pattern: Command Dispatcher (a form of the Strategy Pattern).
    Intent -> Handler function
    The dispatch table makes adding new intents a one-line change.

Phase 4 addition:
    WORKFLOW intent dispatches to the workflow engine instead of a
    simple handler function. The engine receives the executor itself
    so it can reuse all existing handlers for each workflow step.
"""

from jarvis.core.command import (
    Command,
    INTENT_PLAY_MEDIA,
    INTENT_OPEN_APP,
    INTENT_OPEN_WEBSITE,
    INTENT_SEARCH_WEB,
    INTENT_WORKFLOW,
    INTENT_REMEMBER,
    INTENT_RECALL,
    INTENT_SYSTEM_CONTROL,
    INTENT_FILE_ACTION,
    INTENT_SYSTEM_INFO,
    INTENT_RUN_COMMAND,
)
from jarvis.actions import media, apps, browser
from jarvis.actions import workflow_engine
from jarvis.actions import system_control
from jarvis.actions import file_actions
from jarvis.actions import system_info
from jarvis.actions import shell_runner
from jarvis.core import memory


class ActionExecutor:
    """
    Dispatches a resolved Command to the correct action handler.

    Usage:
        executor = ActionExecutor()
        pipeline.set_executor(executor)
    """

    def execute(self, cmd: Command) -> Command:
        """
        Execute the action described by the Command object.

        Reads cmd.intent and cmd.entities, calls the correct handler,
        and writes success + response back to the Command object.

        Args:
            cmd: A Command object with intent and entities already filled in.

        Returns:
            The same Command object, now with success and response set.
        """
        intent = cmd.intent

        # -- Phase 5: REMEMBER intent -----------------------------------------
        if intent == INTENT_REMEMBER:
            key   = cmd.entities.get("key", "")
            value = cmd.entities.get("value", "")
            if not key or not value:
                cmd.success  = False
                cmd.response = "I didn't catch what to remember. Try: 'my name is Rohan'"
            else:
                cmd.success, cmd.response = memory.remember(key, value)
            memory.increment_stat("REMEMBER")
            return cmd

        # -- Phase 5: RECALL intent -------------------------------------------
        if intent == INTENT_RECALL:
            key = cmd.entities.get("key", "all")
            if key == "all":
                cmd.success, cmd.response = memory.recall_all()
            else:
                cmd.success, cmd.response = memory.recall(key)
            memory.increment_stat("RECALL")
            return cmd

        # -- Phase 4: WORKFLOW intent -----------------------------------------
        if intent == INTENT_WORKFLOW:
            workflow_name = cmd.entities.get("workflow_name", "")
            cmd.success, cmd.response = workflow_engine.run_workflow(
                workflow_name, executor=self
            )
            memory.increment_stat("WORKFLOW")
            return cmd

        # -- Phase 7: SYSTEM_CONTROL intent -----------------------------------
        if intent == INTENT_SYSTEM_CONTROL:
            action = cmd.entities.get("action", "")
            value  = cmd.entities.get("value", "")
            cmd.success, cmd.response = system_control.handle(action, value)
            return cmd

        # -- Phase 7: FILE_ACTION intent --------------------------------------
        if intent == INTENT_FILE_ACTION:
            action = cmd.entities.get("action", "open_folder")
            target = cmd.entities.get("target", cmd.entities.get("path", ""))
            cmd.success, cmd.response = file_actions.handle(action, target)
            return cmd

        # -- Phase 7: SYSTEM_INFO intent --------------------------------------
        if intent == INTENT_SYSTEM_INFO:
            metric = cmd.entities.get("metric", "all")
            cmd.success, cmd.response = system_info.handle(metric)
            return cmd

        # -- Phase 7: RUN_COMMAND intent --------------------------------------
        if intent == INTENT_RUN_COMMAND:
            command_name = cmd.entities.get("command_name", "")
            cmd.success, cmd.response = shell_runner.run(command_name)
            return cmd

        # -- Dispatch table ---------------------------------------------------
        dispatch = {
            INTENT_PLAY_MEDIA:   (media.play_media,      "song_name"),
            INTENT_OPEN_APP:     (apps.open_app,         "app_name"),
            INTENT_OPEN_WEBSITE: (browser.open_website,  "website"),
            INTENT_SEARCH_WEB:   (browser.search_web,    "query"),
        }

        if intent not in dispatch:
            cmd.success = False
            cmd.response = "I understood the command but don't know how to execute it yet."
            return cmd

        handler_fn, entity_key = dispatch[intent]
        entity_value = cmd.entities.get(entity_key, "")
        cmd.success, cmd.response = handler_fn(entity_value)

        # Track usage stats
        if cmd.success:
            memory.increment_stat(intent)

        return cmd
