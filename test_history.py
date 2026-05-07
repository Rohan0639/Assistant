import sys
import os
import json
sys.path.insert(0, os.path.abspath(r"C:\Users\chint\Desktop\projects\assistant"))
from jarvis.core import ai_parser

recent_context = [
    "You: play dude ost",
    "JARVIS: Opening YouTube and playing the Dude OST for you"
]

actions, response, emotion = ai_parser.parse("no", recent_context)
print(json.dumps({"actions": actions, "response": response, "emotion": emotion}, indent=2))
