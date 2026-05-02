# J.A.R.V.I.S — Personal AI Desktop Assistant

> **Just A Rather Very Intelligent System**  
> A modular, AI-powered personal assistant for Windows that understands your natural language — including your casual texting style.

---

## ✨ Features

| Category | What JARVIS can do |
|---|---|
| 🎵 **Media** | Play any song on YouTube (`play kesariya`) |
| 🖥️ **Apps** | Launch desktop & Store apps (`open instagram`, `open vs code`) |
| 🌐 **Browser** | Open websites & search (`go to github`, `search python tips`) |
| 🔊 **System Control** | Volume, mute, sleep, shutdown, restart, lock screen |
| 📁 **Files & Folders** | Open Downloads, Desktop, Documents, any folder |
| 📊 **System Info** | Battery, RAM, CPU, disk space (`how's my battery?`) |
| ⌨️ **Shell Commands** | Run whitelisted commands (`run ipconfig`, `ping google`) |
| 🔁 **Workflows** | Multi-step routines (`start coding session`, `morning routine`) |
| 🧠 **Memory** | Remembers your name, preferences across sessions |
| 🤖 **Style Learning** | Learns how *you* type using Gemini — gets smarter over time |

---

## 🧱 Architecture

```
User Input
    │
    ▼
[Chat Logger]  ──── saves every message → learns your style via Gemini
    │
    ▼
[Groq AI Parser (llama-3.3-70b)]
    │   ↑ style profile injected from memory.json
    ▼
[Action Executor]
    ├── media.py          → YouTube
    ├── apps.py           → subprocess / Store apps
    ├── browser.py        → webbrowser
    ├── system_control.py → volume / power / lock
    ├── file_actions.py   → Explorer / os.startfile
    ├── system_info.py    → psutil
    ├── shell_runner.py   → whitelisted commands
    ├── workflow_engine.py→ multi-step chains
    └── memory (REMEMBER/RECALL)
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/jarvis-assistant.git
cd jarvis-assistant
pip install -r requirements.txt
```

### 2. Set API Keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
```

- **Groq** (free): [console.groq.com](https://console.groq.com) — powers all command parsing
- **Gemini** (free): [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) — learns your typing style

### 3. Run

```bash
python jarvis/main.py
```

---

## 🗣️ Example Commands

```
rohan: play arijit singh
rohan: open instagram
rohan: volume up
rohan: how's my battery
rohan: open downloads
rohan: run ipconfig
rohan: start coding session
rohan: my favorite song is kesariya
rohan: what do you know about me?
rohan: shutdown
```

---

## 📁 Project Structure

```
assistant/
├── jarvis/
│   ├── main.py                  # Entry point
│   ├── tray_app.py              # System tray integration
│   ├── core/
│   │   ├── pipeline.py          # Orchestrates all stages
│   │   ├── ai_parser.py         # Groq LLM intent parser
│   │   ├── style_learner.py     # Gemini style extraction
│   │   ├── chat_logger.py       # Conversation history log
│   │   ├── memory.py            # Persistent user memory
│   │   └── command.py           # Command data contract
│   ├── actions/
│   │   ├── executor.py          # Dispatches to handlers
│   │   ├── apps.py              # App launcher
│   │   ├── browser.py           # Web/search opener
│   │   ├── media.py             # YouTube player
│   │   ├── system_control.py    # Volume/power controls
│   │   ├── file_actions.py      # File/folder opener
│   │   ├── system_info.py       # Hardware stats
│   │   ├── shell_runner.py      # Whitelisted shell commands
│   │   └── workflow_engine.py   # Multi-step routines
│   ├── config/
│   │   ├── apps.py              # App registry (add your apps here)
│   │   ├── shell_commands.py    # Shell command whitelist
│   │   ├── workflows.py         # Workflow definitions
│   │   ├── intents.py           # Rule-based intent patterns
│   │   └── memory.json          # Persistent user data
│   └── utils/
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## ⚙️ Configuration

### Add a new app
Edit `jarvis/config/apps.py`:
```python
"my app": r"C:\Path\To\MyApp.exe",
```

### Add a workflow
Edit `jarvis/config/workflows.py`:
```python
"gym mode": [
    {"intent": "PLAY_MEDIA",   "entities": {"song_name": "workout music"}},
    {"intent": "OPEN_WEBSITE", "entities": {"website": "myfitnesspal.com"}},
],
```

### Add a shell command
Edit `jarvis/config/shell_commands.py`:
```python
"my build": ["cmd", "/c", "cd C:\\MyProject && npm run build"],
```

---

## 🔒 Security

- API keys are stored in `.env` — **never committed to git**
- Shell commands use a **strict whitelist** — no arbitrary execution
- Style learning is fully local — only message patterns sent to Gemini, no personal data

---

## 📋 Requirements

- Python 3.11+
- Windows 10/11
- `groq`, `google-genai`, `psutil`, `python-dotenv`, `pystray`, `Pillow`

---

## 🛣️ Roadmap

- [x] Phase 1 — Core pipeline
- [x] Phase 2 — Rule-based parsing
- [x] Phase 3 — Groq AI parser
- [x] Phase 4 — Workflow engine
- [x] Phase 5 — Persistent memory
- [x] Phase 6 — System tray
- [x] Phase 7 — Full OS access
- [x] Style learning via Gemini
- [ ] Voice input (speech-to-text)
- [ ] Reminder & alarm system
- [ ] Plugin system for custom actions

---

## 📄 License

MIT License — free to use, modify, and distribute.
