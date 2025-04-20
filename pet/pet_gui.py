import tkinter as tk
from PIL import Image, ImageTk, ImageSequence # type: ignore
import sys
import os

# Setup for relative import
sys.path.append(os.path.join(os.getcwd(), "pet"))

from pet_state import VirtualPet
from pet_behavior import PetActions

ASSET_PATH = os.path.join("G:/My Drive/AI Projects/virtual-pet/assets", "idle1.gif")

class VirtualPetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Pet Cat")

        self.pet = VirtualPet("Rio")
        self.actions = PetActions(self.pet)

        # Load animated GIF
        self.frames = [ImageTk.PhotoImage(img) for img in ImageSequence.Iterator(Image.open(ASSET_PATH))]
        self.frame_index = 0

        self.canvas = tk.Label(self.root)
        self.canvas.pack()

        self.status_label = tk.Label(self.root, font=("Arial", 12))
        self.status_label.pack()

        # Action buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack()
        tk.Button(btn_frame, text="Feed", command=self.feed).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Play", command=self.play).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Sleep", command=self.sleep).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Wait", command=self.pass_time).pack(side=tk.LEFT)

        self.update_animation()
        self.update_status()

    def update_animation(self):
        self.canvas.configure(image=self.frames[self.frame_index])
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.root.after(100, self.update_animation)

    def update_status(self):
        self.pet.decay()
        status = self.pet.get_status()
        text = f"{status['name']}'s Status\nHunger: {status['hunger']}  Happiness: {status['happiness']}  Energy: {status['energy']}  Mood: {status['mood']}"
        self.status_label.config(text=text)
        self.root.after(1000, self.update_status)

    def feed(self):
        self.actions.feed()

    def play(self):
        self.actions.play()

    def sleep(self):
        self.actions.sleep()

    def pass_time(self):
        self.actions.pass_time()

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualPetApp(root)
    root.mainloop()
