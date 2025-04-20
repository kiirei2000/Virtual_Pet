# pet_behavior.py  – updated for rev‑5 pet_state.py

import random

class PetActions:
    def __init__(self, pet):
        self.pet = pet

    # ---------------- utility ---------------- #
    def _do_action(self, *, hunger=0, happiness=0, energy=0):
        """
        Unified helper:
        • registers the interaction (handles dirty‑bath penalty)
        • applies stat changes with clamping
        """
        self.pet.register_interaction()                    # << NEW
        self.adjust_stats(hunger, happiness, energy)

    def adjust_stats(self, hunger=0, happiness=0, energy=0):
        # clip each stat to [0,20]
        self.pet.hunger     = max(0, min(20, self.pet.hunger     + hunger))
        self.pet.happiness  = max(0, min(20, self.pet.happiness  + happiness))
        self.pet.energy     = max(0, min(20, self.pet.energy     + energy))
        # health is handled inside VirtualPet

    # ---------------- actions ---------------- #
    def feed(self):
        # baseline +1 hunger for any activity, then −3 for feeding
        self._do_action(hunger=-2, happiness=+1, energy=-2)

    def play(self):
        if self.pet.energy < 3:
            print("Too tired to play!")
            return

        success = random.random() < 0.85        # 85 % success rate
        if success:
            self._do_action(hunger=+1, happiness=+2, energy=-3)
        else:
            print("The game fizzled out…")
            self._do_action(hunger=+1, happiness=-1, energy=-3)

    def sleep(self):
        if self.pet.hunger > 10:
            print("Too hungry to sleep!")
            return
        self._do_action(hunger=+1, energy=+5)

    def bath(self):
        # bath() already registers interaction and gives +5 health
        # we still add baseline +1 hunger and optional −1 energy
        self.pet.bath()
        self.adjust_stats(hunger=+1, energy=-1, happiness=-3)

    def pass_time(self):
        """Explicit 'wait' chosen by user. Counted as interaction."""
        self._do_action(hunger=+1)   # baseline only
        # Let decay() run for the idle minute(s)
        self.pet.decay()
