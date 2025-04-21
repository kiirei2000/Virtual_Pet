import tkinter as tk
import random
import threading
import keyboard
from PIL import Image, ImageTk, ImageSequence
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CAT_SCALE = 2
MAX_RIOS = 10

GIFS = {
    "idle": "idle.gif",
    "excited": "excited.gif",
    "cry": "cry.gif",
}

def load_gif(path, scale=1):
    img = Image.open(path)
    frames, delays = [], []
    for frame in ImageSequence.Iterator(img):
        delay = frame.info.get("duration", img.info.get("duration", 100))
        frame = frame.resize((frame.width * scale, frame.height * scale), Image.NEAREST)
        frames.append(ImageTk.PhotoImage(frame.convert("RGBA")))
        delays.append(delay)
    return frames, delays

class RioInstance:
    def __init__(self, master, game, animations, x, y, stay_time_ms):
        self.master = master
        self.game = game
        self.animations = animations
        self.x, self.y = x, y
        self.stay_time_ms = stay_time_ms
        self.hit = False
        self.destroyed = False
        self.state = "idle"
        self.frame_idx = 0
        
        bg_color = "black" if game.borderless else "white"
        self.label = tk.Label(master, bd=0, bg=bg_color, highlightthickness=0)
        
        self.label.place(x=x, y=y)
        self.label.bind("<Button-1>", self.hit_cat)

        self.set_animation("idle")
        self.animate()
        self.timer = self.master.after(stay_time_ms, self.miss_cat)

    def set_animation(self, mood):
        self.frames, self.delays = self.animations[mood]
        self.state = mood
        self.frame_idx = 0
        self.label.config(image=self.frames[0])

    def animate(self):
        if self.state:
            self.label.config(image=self.frames[self.frame_idx])
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
            self.master.after(self.delays[self.frame_idx], self.animate)

    def hit_cat(self, event=None):
        if self.hit or self.destroyed:
            return

        self.hit = True
        self.master.after_cancel(self.timer)
        self.game.adjust_score(+1)
        self.game.adjust_difficulty(success=True)

        self.label.unbind("<Button-1>")
        self.set_animation("cry")
        self.master.after(500, self.destroy)

    def miss_cat(self):
        if self.hit or self.destroyed:
            return

        self.set_animation("excited")
        self.game.adjust_score(-2)
        self.game.adjust_difficulty(success=False)
        self.master.after(500, self.destroy)

    def destroy(self):
        if self.destroyed:
            return
        self.destroyed = True

        try:
            self.label.place_forget()
            self.label.destroy()
        except tk.TclError:
            pass

        self.state = None
        if self in self.game.active_rios:
            self.game.active_rios.remove(self)

class WhacARio:
    def __init__(self):
        self.borderless = False
        self.score = 0
        self.reaction_time = 3000
        self.spawn_interval = 1500
        self.active_rios = []

        self.root = tk.Tk()
        self.setup_normal_mode()

        self.animations = {name: load_gif(ASSETS_DIR / filename, CAT_SCALE) for name, filename in GIFS.items()}
        self.score_label = tk.Label(self.root, text="Score: 0", font=("Arial", 18), bg="white", fg="black")
        self.score_label.pack(anchor="nw", padx=10, pady=10)

        self.spawn_loop()
        threading.Thread(target=self._toggle_listener, daemon=True).start()
        self.root.mainloop()

    def setup_normal_mode(self):
        self.borderless = False
        self.root.title("Whac-a-Rio OSU Mode")
        self.root.geometry("800x600")
        self.root.config(bg="white")
        self.root.overrideredirect(False)
        self.root.wm_attributes("-topmost", False)
        self.root.resizable(False, False)

    def setup_borderless_mode(self):
        self.borderless = True
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.config(bg="black")
        self.root.wm_attributes("-transparentcolor", "black")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

    def _toggle_listener(self):
        keyboard.add_hotkey("alt+shift+m", self.toggle_mode)
        keyboard.wait()

    def toggle_mode(self):
        self.root.after(0, self._toggle_mode_safe)

    def _toggle_mode_safe(self):
        self.score_label.place_forget()
        self.score_label.pack_forget()
        if self.borderless:
            self.setup_normal_mode()
        else:
            self.setup_borderless_mode()
        self.score_label.pack(anchor="nw", padx=10, pady=10)

    def spawn_loop(self):
        if len(self.active_rios) < MAX_RIOS:
            if self.borderless:
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
            else:
                screen_w = 800
                screen_h = 600

            x = random.randint(50, screen_w - 100)
            y = random.randint(100, screen_h - 100)

            rio = RioInstance(self.root, self, self.animations, x, y, self.reaction_time)
            self.active_rios.append(rio)

        next_spawn = max(300, 1500 - (self.score * 30))
        self.root.after(next_spawn, self.spawn_loop)

    def adjust_score(self, delta):
        self.score += delta
        if self.score < 0:
            self.score = 0
        self.score_label.config(text=f"Score: {self.score}")

    def adjust_difficulty(self, success=True):
        if success:
            self.reaction_time = max(500, self.reaction_time - 100)
        else:
            self.reaction_time += 200

if __name__ == "__main__":
    WhacARio()
