"""
tray_app.py

Entry point for running JARVIS in the Windows System Tray with a GUI popup.
Starts minimized to tray. No console window required.
"""

import sys
import os
import threading
import pystray
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import scrolledtext

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jarvis.main import build_pipeline
from jarvis.core import memory

class JarvisTrayApp:
    def __init__(self, root):
        self.root = root
        # Load agent and user names from persistent memory
        agent_name = memory.get_agent_name()
        self.root.title(agent_name)
        self.root.geometry("500x400")
        self.root.configure(bg="#1e1e1e")
        self.root.attributes("-topmost", True)
        
        # Hide the window initially
        self.root.withdraw()
        
        # Handle window close (X button) to just hide it
        self.root.protocol("WM_DELETE_WINDOW", self.hide_interface)

        # Initialize pipeline without blocking input
        self.pipeline = build_pipeline()
        self.icon = None

        self._build_ui()
        self._initial_greeting()

    def _build_ui(self):
        """Build the tkinter UI components."""
        # Input Frame (pack at BOTTOM first)
        input_frame = tk.Frame(self.root, bg="#333333")
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X, side=tk.BOTTOM)

        self.input_entry = tk.Entry(
            input_frame, bg="#333333", fg="#ffffff", font=("Consolas", 12),
            borderwidth=0, highlightthickness=0, insertbackground="white"
        )
        self.input_entry.pack(padx=10, pady=10, fill=tk.X, side=tk.LEFT, expand=True)
        self.input_entry.bind("<Return>", self.handle_input)

        # Output Text Area (pack at TOP)
        self.chat_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg="#1e1e1e", fg="#ffffff", 
            font=("Consolas", 11), borderwidth=0, highlightthickness=0
        )
        self.chat_area.pack(padx=10, pady=(10, 5), fill=tk.BOTH, expand=True, side=tk.TOP)
        self.chat_area.config(state=tk.DISABLED)

    def _initial_greeting(self):
        """Show initial personalized greeting."""
        agent_name = memory.get_agent_name()
        name = memory.get_user_name()
        last = memory.get("last_seen")
        if name and last:
            greeting = f"Welcome back, {name}! Last seen: {last}."
        elif name:
            greeting = f"Hello, {name}! Ready when you are."
        else:
            greeting = f"Hey! I'm {agent_name}. Tell me your name to get started — or just ask me anything."

        self._append_to_chat(agent_name, greeting, is_system=True, mode="chat")
        memory.update_last_seen()

    def create_default_icon(self):
        """Generate a basic default icon if none is provided."""
        image = Image.new('RGB', (64, 64), color=(30, 30, 30))
        draw = ImageDraw.Draw(image)
        # Draw a simple 'J'
        draw.text((22, 10), "J", fill=(0, 200, 255), size=40)
        return image

    def show_interface(self, icon=None, item=None):
        """Open or focus the Tkinter input interface. Called from pystray thread."""
        # Schedule the UI update on the main thread safely
        self.root.after(0, self._show_interface_sync)

    def _show_interface_sync(self):
        """Synchronous part of showing the interface in the main thread."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.input_entry.focus_set()

    def hide_interface(self):
        """Hide the Tkinter window instead of destroying it completely."""
        self.root.withdraw()

    def _append_to_chat(self, sender, message, is_system=False, mode="action"):
        """Helper to append text to the chat area with mode-aware styling."""
        self.chat_area.config(state=tk.NORMAL)

        if sender == "You":
            # User messages: cyan
            sender_color = "#00c8ff"
        elif mode == "chat":
            # Conversational JARVIS reply: soft assistant-blue, no prefix
            sender_color = "#7eb8f7"
        elif is_system:
            # System messages (greeting, startup): bright green
            sender_color = "#00ff7f"
        else:
            # Action responses: green (success) or orange-red (failure)
            sender_color = "#00e676" if is_system else "#ff6b6b"
            # Re-evaluate: is_system is passed as cmd.success for action responses
            # (naming is historical). Reuse the value correctly:
            sender_color = "#00e676" if is_system else "#ff7043"

        # Format the message body
        if sender == "JARVIS" and mode == "chat":
            body = f"{message}\n\n"
        elif sender == "JARVIS":
            prefix = "✓" if is_system else "✗"
            body = f"{prefix} {message}\n\n"
        else:
            body = f"{message}\n\n"

        tag = f"sender_{sender}_{mode}"
        self.chat_area.insert(tk.END, f"{sender}: ", (tag,))
        self.chat_area.insert(tk.END, body)
        self.chat_area.tag_config(tag, foreground=sender_color, font=("Consolas", 11, "bold"))
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def handle_input(self, event=None):
        """Process the user's input through the JARVIS pipeline."""
        raw = self.input_entry.get().strip()
        if not raw:
            return

        self.input_entry.delete(0, tk.END)
        self._append_to_chat("You", raw, mode="action")

        # Run pipeline process in a separate thread so it doesn't freeze the GUI
        threading.Thread(target=self._process_command_thread, args=(raw,), daemon=True).start()

    def _process_command_thread(self, raw):
        """Background thread to process the command and update GUI safely."""
        try:
            cmd = self.pipeline.process(raw)
            if cmd.mode == "chat":
                # Conversational reply — no prefix, different color
                self.root.after(
                    0, self._append_to_chat, "JARVIS", cmd.response, True, "chat"
                )
            else:
                # Action response — keep existing success/failure styling
                self.root.after(
                    0, self._append_to_chat, "JARVIS", cmd.response, cmd.success, "action"
                )
        except Exception as e:
            self.root.after(0, self._append_to_chat, "JARVIS", f"Error: {str(e)}", False, "action")

    def exit_app(self, icon=None, item=None):
        """Cleanly shut down the application from the tray."""
        if self.icon:
            self.icon.stop()
        self.root.after(0, self.root.destroy)
        self.root.after(100, lambda: sys.exit(0))

    def setup_tray(self):
        """Configure and start the system tray icon in a background thread."""
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jarvis.ico")
        if os.path.exists(icon_path):
            image = Image.open(icon_path)
        else:
            image = self.create_default_icon()

        menu = pystray.Menu(
            pystray.MenuItem("Open JARVIS", self.show_interface, default=True),
            pystray.MenuItem("Exit", self.exit_app)
        )

        self.icon = pystray.Icon("JARVIS", image, "JARVIS Assistant", menu)
        
        # Run pystray in a background thread
        threading.Thread(target=self.icon.run, daemon=True).start()

def run_background():
    root = tk.Tk()
    app = JarvisTrayApp(root)
    app.setup_tray()
    # Start the Tkinter main loop in the main thread
    root.mainloop()

if __name__ == "__main__":
    run_background()
