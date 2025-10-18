import math
import matplotlib.pyplot as plt

def wykresy(dane):        
    # --- PRZYGOTOWANIE DANYCH ---
    frames = list(range(len(dane)))
    lengths = [n for (_, _, n, _, _) in dane]

    # odległość euklidesowa między głową a jedzeniem
    distances = [
        math.sqrt((fx - x)**2 + (fy - y)**2)
        for (x, y, _, fx, fy) in dane
    ]

    # --- RYSOWANIE ---
    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.plot(frames, lengths, marker='o', color='green')
    plt.title("Długość węża w czasie")
    plt.xlabel("Klatka / krok gry")
    plt.ylabel("Długość")

    plt.subplot(1, 2, 2)
    plt.plot(frames, distances, marker='x', color='red')
    plt.title("Odległość głowy od jedzenia")
    plt.xlabel("Klatka / krok gry")
    plt.ylabel("Odległość (euklidesowa)")

    plt.tight_layout()
    plt.show()

