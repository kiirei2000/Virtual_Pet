# pet_state.py – rev‑5 (2025‑04‑20)
"""
Adds:  • needs_bath penalty – 50 % chance to lose –1 Health on every
         explicit user action while needs_bath == True
"""

from __future__ import annotations
import time, random
from typing import Dict

MAX_STAT, MIN_STAT = 20, 0
DIRTY_PENALTY_CHANCE = 0.50      # 50 %   tweak as desired


class VirtualPet:
    # ---------------- initialisation ---------------- #
    def __init__(self, name: str = "Rio") -> None:
        self.name = name
        self.hunger = 5
        self.happiness = 10
        self.energy = 10
        self.health = 15

        now = time.time()
        self.last_update = now
        self.last_interaction = now

        self.needs_bath = False
        self._bath_timestamp: float | None = None

    # ---------------- public helpers ---------------- #
    def get_status(self) -> Dict[str, int | str]:
        return {
            "name": self.name,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "energy": self.energy,
            "health": self.health,
            "mood": self.evaluate_mood(),
        }

    def register_interaction(self) -> None:
        """Call from *every* explicit user action (feed, play, sleep, …)."""
        self.last_interaction = time.time()

        # --- dirty penalty -------------------------------------------
        if self.needs_bath and random.random() < DIRTY_PENALTY_CHANCE:
            self._adjust_stat("health", -1)

    def bath(self) -> None:
        self.register_interaction()            # counts as an action
        self.needs_bath = False
        self._adjust_stat("health", +5)
        self._bath_timestamp = time.time()

    # ---------------- decay loop -------------------- #
    def decay(self) -> None:
        now = time.time()
        mins = int((now - self.last_update) // 60)
        if mins <= 0:
            return

        for _ in range(mins):
            self._idle_tick()

        self.last_update += mins * 60

        # Re‑enable dirtiness 5 min after last bath
        if not self.needs_bath and self._bath_timestamp:
            if now - self._bath_timestamp >= 5 * 60:
                self.needs_bath = True

    # ---------------- mood logic -------------------- #
    def evaluate_mood(self) -> str:
        if self.health <= 0:
            return "Dead"
        if self.health < 5:
            return "Sick"

        idle_sec = time.time() - self.last_interaction

        if self.happiness < 5:
            return "Cry"
        if self.happiness < 10:
            return "Sad"
        if self.hunger > 10:
            return "Hungry"
        if self.energy < 5 and self.hunger <= 10:
            return "Sleepy"
        if idle_sec >= 120:
            return "Bored"
        if self.happiness > 10 and self.energy > 10 and self.health > 10 and self.hunger < 10:
            return "Happy"
        return "Idle"

    # ---------------- private helpers --------------- #
    def _idle_tick(self) -> None:
        self._adjust_stat("hunger", +1)
        self._adjust_stat("happiness", -1)
        self._adjust_stat("energy", random.randint(-1, 1))

        if self.hunger > 15:
            self._adjust_stat("health", -3)

    def _adjust_stat(self, attr: str, delta: int) -> None:
        old = getattr(self, attr)
        new = max(MIN_STAT, min(MAX_STAT, old + delta))
        setattr(self, attr, new)

        # reachability of death message
        if attr == "health" and new == 0 and old > 0:
            print(f"{self.name} has died.")
