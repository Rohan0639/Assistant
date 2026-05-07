import sys
sys.path.insert(0, '.')
from jarvis.core import command
from jarvis.core import chat_responder
from jarvis.core import chat_memory_extractor
from jarvis.core import ai_parser
from jarvis.core import pipeline
import jarvis.tray_app
print('All modules imported successfully!')
c = command.Command("test")
print("Command.mode default:", repr(c.mode))
print("chat_responder available:", chat_responder.is_available())
