import tkinter as tk
import random
import time
import threading
import keyboard # type: ignore[import]
from PIL import Image, ImageTk, ImageSequence
from pathlib import Path
import sys

# ─── Configuration ─────────────────────────────
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CAT_SCALE = 2
MAX_POKE_PER_MIN = 10
MOOD_GIFS = {
    "idle":      "idle.gif",
    "excited":   "excited.gif",
    "surprised": "surprised.gif",
    "dance":     "dance.gif",
    "sleepy":    "sleepy.gif",
    "sleep":     "sleep.gif",
    "eating":    "eating.gif",
    "laydown":   "laydown.gif",
    "sad":       "sad.gif",
    "box":       "box.gif",
    "waiting":   "waiting.gif",
    "cry":       "cry.gif",
}
EXCLUDED_FROM_RANDOM = {"cry"}

# ─── GIF Loader ────────────────────────────────
def load_gif(path, scale=1):
    img = Image.open(path)
    frames, delays = [], []
    for frame in ImageSequence.Iterator(img):
        delay = frame.info.get('duration', img.info.get('duration', 100))
        frame = frame.resize((frame.width * scale, frame.height * scale), Image.NEAREST)
        frames.append(ImageTk.PhotoImage(frame.convert("RGBA")))
        delays.append(delay)
    return frames, delays

# ─── Floating Cat App ──────────────────────────
class FloatingCat:
    def __init__(self):
        self.state = "idle"
        self.recovering = False
        self.visible = True
        self.dragging = False
        self.last_pokes = []
        self.last_interaction = time.time()

        # ─ GUI Setup ─
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "white")
        self.root.config(bg="white")

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        self.label = tk.Label(self.root, bg="white", bd=0)
        self.label.pack()

        self.label.bind("<Button-1>", self._on_click_left)
        self.label.bind("<Button-3>", self._on_click_right)
        self.label.bind("<B1-Motion>", self._on_drag)
        self.label.bind("<ButtonRelease-1>", self._on_release)

        self.animations = {k: load_gif(ASSETS_DIR / v, CAT_SCALE) for k, v in MOOD_GIFS.items()}
        self._set_mood("idle")
        self._move_to_random_location()

        # ─ Start Timers & Threads ─
        self._animate()
        self._schedule_idle_check()
        self._schedule_auto_move()
        self._schedule_mood_switch()
        self.root.after(1000, lambda: threading.Thread(target=self._toggle_listener, daemon=True).start())

        self.root.mainloop()

    # ─── Mood Control ───────────────────────────
    def _set_mood(self, mood):
        self.state = mood
        self.frames, self.delays = self.animations[mood]
        self.frame_idx = 0
        self.label.configure(image=self.frames[0])

    def _animate(self):
        self.label.configure(image=self.frames[self.frame_idx])
        delay = self.delays[self.frame_idx]
        self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        self.root.after(delay, self._animate)

    def _recover_from_cry(self):
        self._set_mood("idle")
        self.recovering = False
        self.last_interaction = time.time()

    # ─── Interactions ───────────────────────────
    def _on_click_left(self, event):
        if self.recovering:
            return

        now = time.time()
        self.last_interaction = now
        self.last_pokes = [t for t in self.last_pokes if now - t <= 60]
        self.last_pokes.append(now)

        if len(self.last_pokes) > MAX_POKE_PER_MIN:
            self.recovering = True
            self._set_mood("cry")
            self.root.after(5000, lambda: self._set_mood("sad"))
            self.root.after(10000, self._recover_from_cry)
            self.last_pokes.clear()
        else:
            self._set_mood("laydown")

        self.drag_offset_x = event.x
        self.drag_offset_y = event.y
        self.dragging = False

    def _on_click_right(self, event):
        self.root.destroy()

    def _on_drag(self, event):
        x = self.root.winfo_pointerx() - self.drag_offset_x
        y = self.root.winfo_pointery() - self.drag_offset_y
        self.root.geometry(f"+{x}+{y}")
        self.dragging = True

    def _on_release(self, event):
        self.dragging = False

    # ─── Idle & Mood Switch ─────────────────────
    def _schedule_idle_check(self):
        now = time.time()
        idle_time = now - self.last_interaction
        if self.state not in {"cry", "sad"}:
            if idle_time > 600 and self.state != "sleep":
                self._set_mood("sleep")
            elif idle_time > 300 and self.state not in {"laydown", "sleep"}:
                self._set_mood("laydown")
        self.root.after(10000, self._schedule_idle_check)

    def _schedule_mood_switch(self):
        if self.state not in {"sleep", "laydown", "cry", "sad"} and not self.dragging:
            new_mood = random.choice([m for m in MOOD_GIFS if m not in EXCLUDED_FROM_RANDOM])
            self._set_mood(new_mood)
        self.root.after(random.randint(5000, 10000), self._schedule_mood_switch)

    def _schedule_auto_move(self):
        if not self.dragging:
            self._move_to_random_location()
        self.root.after(60000, self._schedule_auto_move)

    def _move_to_random_location(self):
        w, h = self.frames[0].width(), self.frames[0].height()
        x = random.randint(0, self.screen_w - w)
        y = random.randint(0, self.screen_h - h)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ─── Global Hotkey ──────────────────────────
    def _toggle_listener(self):
        try:
            keyboard.add_hotkey("alt+Q", self._toggle_visibility)
        except Exception as e:
            print("Keyboard hotkey listener failed:", e, file=sys.stderr)

    def _toggle_visibility(self):
        self.visible = not self.visible
        if self.visible:
            self.root.after(0, self.root.deiconify)
        else:
            self.root.after(0, self.root.withdraw)

# ─── Launch ─────────────────────────────────────
if __name__ == "__main__":
    FloatingCat()
