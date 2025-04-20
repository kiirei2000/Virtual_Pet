# main.py – CLI test harness for VirtualPet rev‑5

from pet.pet_state import VirtualPet
from pet.pet_behavior import PetActions
import time

def display_status(pet: VirtualPet):
    s = pet.get_status()
    print(f"\n{s['name']}'s Status:")
    print(f"Hunger: {s['hunger']}")
    print(f"Happiness: {s['happiness']}")
    print(f"Energy: {s['energy']}")
    print(f"Health: {s['health']}")
    print(f"Mood: {s['mood']}")

def main():
    pet = VirtualPet("Rio")
    actions = PetActions(pet)

    while True:
        pet.decay()           # advance time
        display_status(pet)

        print("\nChoose an action:")
        print("1. Feed")
        print("2. Play")
        print("3. Sleep")
        print("4. Bath")
        print("5. Wait (pass time)")
        print("6. Exit")
        choice = input(">> ")

        if choice == "1":
            actions.feed()
        elif choice == "2":
            actions.play()
        elif choice == "3":
            actions.sleep()
        elif choice == "4":
            actions.bath()
        elif choice == "5":
            actions.pass_time()
        elif choice == "6":
            break
        else:
            print("Invalid choice.")

        time.sleep(1)

if __name__ == "__main__":
    main()