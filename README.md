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
| 🧠 **Memory** | Remembers your name, preferences, and facts across sessions |
| 🤖 **Style Learning** | Learns how *you* type using Gemini — gets smarter over time |
| 💬 **Conversational** | Witty, warm chat mode powered by Groq (llama-3.3-70b) |

---

## 🧱 Architecture

JARVIS uses a hybrid pipeline that prioritizes AI understanding but falls back to robust rule-based parsing.

```
[User Input]
     │
     ▼
[Pipeline Orchestrator]
     │
     ├─[Stage 1: Input Handler]─── Normalizes text (case, spacing)
     │
     ├─[Stage 2: AI Path] (Primary)
     │    ├─[Chat Logger]───────── Logs history for style learning
     │    ├─[AI Parser (Groq)]──── Intent + Entity extraction via Llama 3.3
     │    └─[Style Learner (Gemini)] Extracts your typing profile
     │
     ├─[Stage 3: Fallback Path] (Offline/Rules)
     │    ├─[Preprocessor]──────── Removes noise / stop words
     │    ├─[Intent Parser]─────── Regex-based classification
     │    └─[Entity Extractor]──── Keyword-based entity extraction
     │
     ▼
[Action Executor]
     ├── media.py          → YouTube integration
     ├── apps.py           → Subprocess / Windows Store apps
     ├── browser.py        → Webbrowser automation
     ├── system_control.py → Volume / Power / Lock controls
     ├── file_actions.py   → Explorer / OS integration
     ├── system_info.py    → Hardware stats (psutil)
     ├── shell_runner.py   → Whitelisted command execution
     └── workflow_engine.py→ Multi-step routine coordinator
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/jarvis-assistant.git
cd jarvis-assistant
# Recommended: Create a virtual environment
python -m venv .venv
.venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
```

### 2. Set API Keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
```

- **Groq** (free): [console.groq.com](https://console.groq.com) — Powers all command parsing and conversational chat.
- **Gemini** (free): [aistudio.google.com](https://aistudio.google.com/app/apikey) — Learns your typing style for personalized interactions.

### 3. Run

**CLI Mode:**
```bash
python jarvis/main.py
```

**System Tray Mode (GUI):**
```bash
python jarvis/tray_app.py
```

### 🔨 Building (.exe)

To build the standalone Windows executable:
```bash
.\scripts\build_tray.bat
```
The resulting file will be in the `dist/` folder.

---

## 📁 Project Structure

```
assistant/
├── .venv/                       # Python virtual environment
├── build/                       # PyInstaller build artifacts
├── dist/                        # Compiled executables
├── docs/                        # Documentation
│   └── jarvis_assistant_roadmap.pdf
├── jarvis/                      # Core Source Code
│   ├── main.py                  # CLI Entry point
│   ├── tray_app.py              # System tray integration (GUI)
│   ├── core/                    # Intelligence Layer
│   │   ├── pipeline.py          # Orchestrates all stages
│   │   ├── ai_parser.py         # Groq LLM intent parser
│   │   ├── groq_client.py       # Wrapper for Groq API
│   │   ├── chat_responder.py    # Conversational chat logic
│   │   ├── style_learner.py     # Gemini style extraction
│   │   ├── chat_logger.py       # Conversation history log
│   │   ├── memory.py            # Persistent user memory
│   │   ├── chat_memory_extractor.py # Background memory extraction
│   │   ├── entity_extractor.py  # Rule-based entity extraction
│   │   ├── intent_parser.py     # Rule-based intent parsing
│   │   ├── preprocessor.py      # Input cleaning for rules
│   │   ├── input_handler.py     # Initial text normalization
│   │   └── command.py           # Command data contract & constants
│   ├── actions/                 # Execution Layer
│   │   ├── executor.py          # Dispatches to handlers
│   │   ├── workflow_engine.py   # Multi-step routines coordinator
│   │   ├── apps.py              # App launcher
│   │   ├── browser.py           # Web/search opener
│   │   ├── media.py             # YouTube player
│   │   ├── system_control.py    # Volume/power controls
│   │   ├── file_actions.py      # File/folder opener
│   │   ├── system_info.py       # Hardware stats
│   │   └── shell_runner.py      # Whitelisted shell commands
│   ├── config/                  # User Configuration
│   │   ├── apps.py              # App registry (add your apps here)
│   │   ├── shell_commands.py    # Shell command whitelist
│   │   ├── workflows.py         # Workflow definitions
│   │   ├── intents.py           # Rule-based intent patterns
│   │   └── memory.json          # Persistent user data (auto-updated)
│   └── utils/                   # Shared utilities
├── scripts/                     # Build & Utility scripts
│   └── build_tray.bat
├── .env                         # API Keys (Local only)
├── .env.example                 # Template for API keys
├── .gitignore                   # Git exclusions
├── JARVIS.spec                  # PyInstaller build spec
├── README.md                    # This file
├── requirements-tray.txt        # Tray-specific dependencies
└── requirements.txt             # Full project dependencies
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

- **Local First**: Your memory and logs are stored locally in `jarvis/config/`.
- **API Privacy**: Only message patterns are sent to Gemini for style learning; no sensitive data is exported.
- **Whitelisting**: Shell commands use a strict whitelist to prevent accidental execution of harmful commands.
- **Environment Safety**: API keys are managed via `.env` and excluded from version control.

---

## 🛣️ Roadmap

- [x] Phase 1-3 — Core AI Pipeline & Rule-based fallbacks
- [x] Phase 4 — Multi-step Workflow Engine
- [x] Phase 5 — Persistent Memory (Name, preferences)
- [x] Phase 6 — System Tray Integration
- [x] Phase 7 — Advanced OS Control (Volume, Power, Hardware Info)
- [x] Phase 8 — Conversational Chat Mode & Style Learning
- [ ] Voice input (Speech-to-Text)
- [ ] Visual Dashboard for status monitoring
- [ ] Plugin system for custom user modules

---

## 📄 License

MIT License — Free to use, modify, and distribute.

