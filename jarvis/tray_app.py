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
        self.root.title("JARVIS")
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
        # Output Text Area
        self.chat_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg="#1e1e1e", fg="#ffffff", 
            font=("Consolas", 11), borderwidth=0, highlightthickness=0
        )
        self.chat_area.pack(padx=10, pady=(10, 5), fill=tk.BOTH, expand=True)
        self.chat_area.config(state=tk.DISABLED)

        # Input Frame
        input_frame = tk.Frame(self.root, bg="#333333")
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        self.input_entry = tk.Entry(
            input_frame, bg="#333333", fg="#ffffff", font=("Consolas", 12),
            borderwidth=0, highlightthickness=0, insertbackground="white"
        )
        self.input_entry.pack(padx=10, pady=10, fill=tk.X, side=tk.LEFT, expand=True)
        self.input_entry.bind("<Return>", self.handle_input)

    def _initial_greeting(self):
        """Show initial personalized greeting."""
        name = memory.get_user_name()
        last = memory.get("last_seen")
        if name and last:
            greeting = f"Welcome back, {name}! (Last seen: {last})"
        elif name:
            greeting = f"Hello, {name}! Good to see you."
        else:
            greeting = "Ready. Tell me your name to get started!"
        
        self._append_to_chat("JARVIS", greeting, is_system=True)
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

    def _append_to_chat(self, sender, message, is_system=False):
        """Helper to append text to the chat area."""
        self.chat_area.config(state=tk.NORMAL)
        if sender == "You":
            color = "#00c8ff" # Cyan for user
        else:
            color = "#00ff00" if is_system else "#aaaaaa" # Green or Gray for JARVIS
            
        self.chat_area.insert(tk.END, f"{sender}: ", ("sender",))
        self.chat_area.insert(tk.END, f"{message}\n\n")
        
        self.chat_area.tag_config("sender", foreground=color, font=("Consolas", 11, "bold"))
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def handle_input(self, event=None):
        """Process the user's input through the JARVIS pipeline."""
        raw = self.input_entry.get().strip()
        if not raw:
            return

        self.input_entry.delete(0, tk.END)
        self._append_to_chat("You", raw)

        # Run pipeline process in a separate thread so it doesn't freeze the GUI
        threading.Thread(target=self._process_command_thread, args=(raw,), daemon=True).start()

    def _process_command_thread(self, raw):
        """Background thread to process the command and update GUI safely."""
        try:
            cmd = self.pipeline.process(raw)
            prefix = "[OK]" if cmd.success else "[!]"
            response = f"{prefix} {cmd.response}"
            # Update GUI from the main thread safely
            self.root.after(0, self._append_to_chat, "JARVIS", response, cmd.success)
        except Exception as e:
            self.root.after(0, self._append_to_chat, "JARVIS", f"Error: {str(e)}", False)

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
