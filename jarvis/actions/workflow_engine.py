"""
actions/workflow_engine.py

Phase 4 -- Multi-step workflow execution engine.

Responsibility:
    Given a workflow name, look it up in config/workflows.py,
    then execute each step sequentially using the existing action handlers.

Design principle:
    The engine does NOT know what actions exist. It creates a mini Command
    object per step and delegates execution to the same ActionExecutor
    already used by the main pipeline. Zero code duplication.

Fuzzy matching:
    "coding" -> looks up WORKFLOW_ALIASES -> "coding session" -> runs workflow
    This means you don't have to say the exact name.
"""

from jarvis.core.command import Command, INTENT_UNKNOWN
from jarvis.config.workflows import WORKFLOWS, WORKFLOW_ALIASES


def _resolve_workflow_name(raw_name: str) -> str | None:
    """
    Resolve a raw workflow name to a canonical key in WORKFLOWS.

    Lookup order:
        1. Exact match in WORKFLOWS
        2. Exact match in WORKFLOW_ALIASES -> canonical name
        3. Partial match: any WORKFLOWS key starts with raw_name
        4. Partial match: raw_name found inside any WORKFLOWS key

    Returns:
        Canonical workflow name if found, else None.
    """
    key = raw_name.lower().strip()

    # Tier 1: Exact match
    if key in WORKFLOWS:
        return key

    # Tier 2: Alias lookup
    if key in WORKFLOW_ALIASES:
        canonical = WORKFLOW_ALIASES[key]
        if canonical in WORKFLOWS:
            return canonical

    # Tier 3: Partial starts-with match
    for name in WORKFLOWS:
        if name.startswith(key):
            return name

    # Tier 4: Substring match
    for name in WORKFLOWS:
        if key in name:
            return name

    return None


def run_workflow(workflow_name: str, executor) -> tuple[bool, str]:
    """
    Execute a named workflow by running its steps through the executor.

    Args:
        workflow_name: The name the AI extracted (may be fuzzy).
        executor:      The ActionExecutor instance (injected, same as pipeline).

    Returns:
        (success, response_message)
        success = True only if ALL steps succeed.

    Example:
        run_workflow("coding session", executor)
        -> Opens Chrome, GitHub, plays focus music
        -> Returns (True, "Workflow 'coding session' complete! (3/3 steps)")
    """
    canonical = _resolve_workflow_name(workflow_name)

    if not canonical:
        known = ", ".join(sorted(WORKFLOWS.keys()))
        return False, (
            f"I don't know the workflow '{workflow_name}'. "
            f"Available workflows: {known}."
        )

    steps = WORKFLOWS[canonical]
    total = len(steps)
    results = []

    print(f"\n  [Workflow] Starting '{canonical}' ({total} steps)")

    for i, step in enumerate(steps, start=1):
        label   = step.get("label", f"Step {i}...")
        intent  = step.get("intent", INTENT_UNKNOWN)
        entities = step.get("entities", {})

        print(f"  [Workflow] Step {i}/{total}: {label}")

        # Build a mini Command object for this step
        mini_cmd = Command(raw_input=f"[workflow step {i}]")
        mini_cmd.intent   = intent
        mini_cmd.entities = entities

        # Delegate to the real executor (reuses all existing action handlers)
        result_cmd = executor.execute(mini_cmd)
        results.append(result_cmd.success)

        status = "[OK]" if result_cmd.success else "[!]"
        print(f"  [Workflow]   {status} {result_cmd.response}")

    succeeded = sum(results)
    all_ok    = all(results)

    summary = (
        f"Workflow '{canonical}' complete! "
        f"({succeeded}/{total} steps succeeded)"
    )
    print()
    return all_ok, summary


def list_workflows() -> str:
    """Return a formatted string listing all available workflows."""
    lines = ["Available workflows:"]
    for name, steps in WORKFLOWS.items():
        lines.append(f"  '{name}' -- {len(steps)} steps")
    return "\n".join(lines)
