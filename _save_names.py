"""Save user_name=Rohan and agent_name=JARVIS to persistent memory."""
import sys
sys.path.insert(0, '.')
from jarvis.core import memory

memory.set("user_name", "Rohan")
memory.set("agent_name", "JARVIS")

print("Saved:")
print("  user_name  =", memory.get("user_name"))
print("  agent_name =", memory.get("agent_name"))
