# room_gui.py – rev‑6 (2025‑04‑20)  ✨ NEW hunger / tired logic
from pathlib import Path
import random, time
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence

from pet.pet_state import VirtualPet              # :contentReference[oaicite:0]{index=0}&#8203;:contentReference[oaicite:1]{index=1}
from pet.pet_behavior import PetActions           # :contentReference[oaicite:2]{index=2}&#8203;:contentReference[oaicite:3]{index=3}

ASSETS          = Path(__file__).resolve().parent / "assets"
CAT_SCALE       = 2
CANVAS_W, CANVAS_H = 512, 512
FLOOR_POLY      = (23, 351, 261, 231, 492, 351, 261, 473)

YAWN_DURATION   = 2          # seconds each yawn
YAWN_INTERVAL   = 10         # seconds between yawns
IDLE_WANDER_MIN = 4
IDLE_WANDER_MAX = 8
TOY_LIFETIME_S  = 5

# ───────────────────────── helpers ─────────────────────────
def load_gif(path: Path, scale: int = 1):
    frames, delays = [], []
    img = Image.open(path)
    for f in ImageSequence.Iterator(img):
        delays.append(f.info.get("duration", img.info.get("duration", 100)))
        if scale != 1:
            f = f.resize((f.width * scale, f.height * scale), Image.NEAREST)
        frames.append(ImageTk.PhotoImage(f.convert("RGBA")))
    return frames, delays

def point_in_poly(x: int, y: int, pts):
    n, inside, j = len(pts)//2, False, (len(pts)//2)-1
    for i in range(n):
        xi, yi = pts[2*i], pts[2*i+1]
        xj, yj = pts[2*j], pts[2*j+1]
        if (yi > y) != (yj > y) and x < (xj-xi)*(y-yi)/((yj-yi) or 1) + xi:
            inside = not inside
        j = i
    return inside

# ───────────────────────── GUI ─────────────────────────
class RoomGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Virtual Cat")

        # model
        self.pet     = VirtualPet("Rio")
        self.actions = PetActions(self.pet)

        # timing flags
        self.busy_until   = 0.0
        self._next_wander = time.time() + random.uniform(IDLE_WANDER_MIN, IDLE_WANDER_MAX)
        self._last_yawn   = 0.0

        # canvas + background
        self.canvas = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H, highlightthickness=0)
        self.canvas.pack()
        bg = ImageTk.PhotoImage(Image.open(ASSETS / "RoomExample.png"))
        self.canvas.create_image(0, 0, anchor="nw", image=bg)
        self.bg_img = bg                                 # keep reference

        # debug bar toggle with D
        self._debug_visible = True
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(root, textvariable=self.status_var,
                                     font=("Consolas", 10), bg="lightyellow", anchor="w")
        self.status_label.place(x=0, y=0, width=CANVAS_W)
        root.bind("<d>", self._toggle_debug); root.bind("<D>", self._toggle_debug)

        # hotspots (click targets)
        self._add_hotspot(237, 419, "bowl_food")
        self._add_hotspot(298, 402, "bowl_water")
        self._add_hotspot(163, 349, "ball")
        self._add_hotspot(158, 317, "ball_alt")
        self._add_hotspot(259, 263, "bed")
        self._add_hotspot(350, 284, "mouse")
        self._add_hotspot(420, 326, "toy_wand")
        self._add_hotspot(451, 213, "bath")

        # shower prop
        shower = ImageTk.PhotoImage(Image.open(ASSETS / "shower.png"))
        self.canvas.create_image(451, 213, anchor="center", image=shower)
        self.shower_img = shower

        # animations
        self.animations = {
            "idle":     load_gif(ASSETS / "idle.gif",    CAT_SCALE),
            "laydown":  load_gif(ASSETS / "laydown.gif", CAT_SCALE),  # NEW
            "eating":   load_gif(ASSETS / "eating.gif",  CAT_SCALE),
            "sleepy":   load_gif(ASSETS / "sleepy.gif",  CAT_SCALE),
            "sleep":    load_gif(ASSETS / "sleep.gif",   CAT_SCALE),
            "dance":    load_gif(ASSETS / "dance.gif",   CAT_SCALE),
            "bath":     load_gif(ASSETS / "bath.gif",    CAT_SCALE),
        }
        self.toy_anims = {
            "ball":  load_gif(ASSETS / "BlueBall.gif", CAT_SCALE),
            "mouse": load_gif(ASSETS / "mouse.gif"),   # intentionally un‑scaled
        }

        self.state     = "idle"
        self.frame_idx = 0
        self.default_x = CANVAS_W // 2
        self.floor_y   = int(CANVAS_H * 0.76)
        first_frame    = self.animations["idle"][0][0]
        self.cat_id    = self.canvas.create_image(self.default_x, self.floor_y,
                                                  anchor="s", image=first_frame, tags=("cat",))

        # loops
        self.canvas.bind("<Button-1>", self._on_click)
        self.root.after(self.animations["idle"][1][0], self._animate)
        self.root.after(1000, self._game_tick)

    # ───────── helpers ─────────
    def _toggle_debug(self, *_):
        self._debug_visible = not self._debug_visible
        if self._debug_visible:
            self.status_label.place(x=0, y=0, width=CANVAS_W)
        else:
            self.status_label.place_forget()

    def _add_hotspot(self, x, y, tag):
        self.canvas.create_oval(x-16, y-16, x+16, y+16, outline="", fill="", tags=(tag,))

    def _set_state(self, name):
        if name != self.state:
            self.state, self.frame_idx = name, 0
            self.canvas.itemconfig(self.cat_id, image=self.animations[name][0][0])

    # ───────── animation loop ─────────
    def _animate(self):
        frames, delays = self.animations[self.state]
        self.canvas.itemconfig(self.cat_id, image=frames[self.frame_idx])
        self.root.after(delays[self.frame_idx], self._animate)
        self.frame_idx = (self.frame_idx + 1) % len(frames)

    # ───────── game tick ─────────
    def _game_tick(self):
        self.pet.decay()
        now = time.time()

        # debug bar
        if self._debug_visible:
            st = self.pet.get_status()
            self.status_var.set(
                f"HP:{st['health']:>2}  Hunger:{st['hunger']:>2}  "
                f"Energy:{st['energy']:>2}  Happy:{st['happiness']:>2}"
            )

        # action blocking
        if now < self.busy_until:
            self.root.after(1000, self._game_tick); return

        # ─── state logic ───
        is_hungry = self.pet.hunger > 5
        is_tired  = self.pet.energy < 5 and not is_hungry   # hungry overrides tired

        if is_hungry:
            # lock cat to bowl position
            self.canvas.coords(self.cat_id, 237+12, 419)
            self._set_state("laydown")

        elif is_tired:
            # yawn every YAWN_INTERVAL
            if now - self._last_yawn >= YAWN_INTERVAL:
                self._set_state("sleepy")
                self.busy_until = now + YAWN_DURATION
                self._last_yawn = now
            else:
                self._set_state("idle")
        else:
            # normal idle + wandering
            if self.state == "idle" and now >= self._next_wander:
                nx, ny = self._random_floor_point()
                self.canvas.coords(self.cat_id, nx, ny)
                self._next_wander = now + random.uniform(IDLE_WANDER_MIN, IDLE_WANDER_MAX)
            self._set_state("idle")

        self.root.after(1000, self._game_tick)

    # ───────── click handler ─────────
    BED_X, BED_Y = 259, 263
    BATH_X, BATH_Y = 420, 272
    EAT_X, EAT_Y = 206, 396
    def _on_click(self, event):
        now = time.time()
        if now < self.busy_until:
            return

        # item under cursor?
        clicked_tag = None
        for item in self.canvas.find_overlapping(event.x, event.y, event.x, event.y):
            if (tags := self.canvas.gettags(item)):
                clicked_tag = tags[0]; break

        is_hungry = self.pet.hunger > 10
        is_tired  = self.pet.energy < 5 and not is_hungry

        # floor movement disabled while hungry
        def can_move_floor():
            return not is_hungry and point_in_poly(event.x, event.y, FLOOR_POLY)

        # ─── props ───
        if clicked_tag == "bowl_food":
            if self.pet.health <= 0:
                print("Rio is no longer with us…"); return
            self.actions.feed()
            self._set_state("eating")
            self.canvas.coords(self.cat_id, self.EAT_X, self.EAT_Y)
            self.busy_until = now + 3
        elif clicked_tag == "bed" and is_tired:
            self.actions.sleep()
            self._set_state("sleep")
            self.canvas.coords(self.cat_id, self.BED_X, self.BED_Y)
            self.busy_until = now + 5
        elif clicked_tag == "bath":
            self.actions.bath()
            self._set_state("bath")
            self.canvas.coords(self.cat_id, self.BATH_X, self.BATH_Y)   # ← (move cat under shower)
            self.busy_until = now + 5
        elif clicked_tag in {"ball", "ball_alt"} and not is_hungry:
            self.actions.play()
            self._spawn_toy("ball");   self.busy_until = now + 3
        elif clicked_tag == "mouse" and not is_hungry:
            self.actions.play()
            self._spawn_toy("mouse");  self.busy_until = now + 3
        elif clicked_tag == "cat" and not is_hungry:
            self.actions.play()
            self._set_state("dance");  self.busy_until = now + 3
        elif clicked_tag is None and can_move_floor():
            # move cat freely
            self.canvas.coords(self.cat_id, event.x, event.y)
            self.pet.register_interaction()
            self._next_wander = now + random.uniform(IDLE_WANDER_MIN, IDLE_WANDER_MAX)

    # ───────── toy spawner ─────────
    def _spawn_toy(self, key):
        frames, delays = self.toy_anims[key]
        cx, cy = self.canvas.coords(self.cat_id)
        toy_id = self.canvas.create_image(cx + 32, cy, anchor="s", image=frames[0])

        deadline = time.time() + TOY_LIFETIME_S
        def _anim(idx=0):
            if time.time() >= deadline or not self.canvas.coords(toy_id):
                self.canvas.delete(toy_id); return
            self.canvas.itemconfig(toy_id, image=frames[idx])
            self.root.after(delays[idx], _anim, (idx+1) % len(frames))
        _anim()

    # ───────── misc ─────────
    def _random_floor_point(self):
        while True:
            x = random.randint(23, 492)
            y = random.randint(231, 473)
            if point_in_poly(x, y, FLOOR_POLY):
                return x, y

# ─────────────────────── run standalone ───────────────────────
if __name__ == "__main__":
    RoomGUI(tk.Tk()).root.mainloop()
