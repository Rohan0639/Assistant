from jarvis.core.ai_parser import parse
print(parse("increase volume", recent_context=["JARVIS: [!] I'm not sure what you mean. Try 'play <song>', 'open <app>', 'go to <site>', or 'search <query>'."]))
