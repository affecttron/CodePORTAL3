from task import Task

print("=== TASK KLASES TESTS ===\n")

uzdevums = Task(
    question="x = 10\nif x > 5:\n    print('A')\nelse:\n    print('B')\n\nKas tiks izvadīts?",
    correct_answer="A",
    hint="Pārbaudi vai 10 ir lielāks par 5.",
    points=100
)


print("--- Uzdevums ---")
print(uzdevums.display())
print()


print("--- Getters ---")
print(f"Punkti:      {uzdevums.get_points()}")
print(f"Palīdzība:   {uzdevums.get_hint()}")
print(f"Mēģinājumi:  {uzdevums.get_attempts_used()}")
print()

print("--- Atbilžu pārbaude ---")
print(f"'A':   {uzdevums.verify('A')}        ← jābūt True")
print(f"'a':   {uzdevums.verify('a')}        ← jābūt True (case-insensitive)")
print(f"' A ': {uzdevums.verify(' A ')}      ← jābūt True (atstarpes notīrītas)")
print(f"'B':   {uzdevums.verify('B')}        ← jābūt False")
print(f"'':    {uzdevums.verify('')}         ← jābūt False")
print()


print("--- Mēģinājumu skaitītājs ---")
print(f"Sākumā: {uzdevums.get_attempts_used()}")
uzdevums.increment_attempts()
uzdevums.increment_attempts()
print(f"Pēc 2 mēģinājumiem: {uzdevums.get_attempts_used()}")
uzdevums.reset_attempts()
print(f"Pēc reset: {uzdevums.get_attempts_used()}")
print()


print("--- Punktu aprēķins ---")
print(f"1. mēģinājums, 10 sek: {uzdevums.calculate_points(1, 10)} pts ← 100 + 25 bonus")
print(f"1. mēģinājums, 20 sek: {uzdevums.calculate_points(1, 20)} pts ← 100 (bez bonusa)")
print(f"2. mēģinājums, 5 sek:  {uzdevums.calculate_points(2, 5)} pts  ← 50 + 25 bonus")
print(f"3. mēģinājums, 30 sek: {uzdevums.calculate_points(3, 30)} pts ← 20 (bez bonusa)")
print(f"4. mēģinājums:         {uzdevums.calculate_points(4, 5)} pts  ← 0 (zaudēts)")

print("\n✅ TESTS PABEIGTS!")