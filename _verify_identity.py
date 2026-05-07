"""Verify names are saved and JARVIS identifies itself correctly."""
import sys
sys.path.insert(0, '.')

from jarvis.core import memory, chat_responder

# 1. Check stored names
print("=== Stored Names ===")
print("user_name  :", memory.get_user_name())
print("agent_name :", memory.get_agent_name())

# 2. Test identity question
print("\n=== Identity Test ===")
print('Q: "what is your name?"')
ans = chat_responder.reply("what is your name?")
print("A:", ans)

print('\nQ: "who are you?"')
ans2 = chat_responder.reply("who are you?")
print("A:", ans2)
