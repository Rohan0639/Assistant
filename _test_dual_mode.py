"""
Quick end-to-end test of dual-mode JARVIS pipeline.
Tests chat mode and action mode without launching the GUI.
"""
import sys
sys.path.insert(0, '.')

from jarvis.main import build_pipeline

pipeline = build_pipeline()

tests = [
    # (input, expected_mode, description)
    ("how are you?",             "chat",   "Pure chat - greeting"),
    ("tell me a joke",           "chat",   "Pure chat - joke request"),
    ("what is 2 + 2?",          "chat",   "Pure chat - math question"),
    ("open chrome",              "action", "Action - open app"),
    ("volume up",                "action", "Action - system control"),
    ("search for python tips",   "action", "Action - web search"),
    ("my friend Rahul called me","chat",   "Chat with personal info"),
    ("what can you do?",         "chat",   "Pure chat - capabilities question"),
]

print("\n" + "="*70)
print("JARVIS Dual-Mode Test")
print("="*70)

for user_input, expected_mode, desc in tests:
    cmd = pipeline.process(user_input)
    status = "PASS" if cmd.mode == expected_mode else "FAIL"
    print(f"\n[{status}] {desc}")
    print(f"  Input:    {user_input!r}")
    print(f"  Mode:     {cmd.mode!r}  (expected: {expected_mode!r})")
    print(f"  Response: {cmd.response[:100]}...")

print("\n" + "="*70)
