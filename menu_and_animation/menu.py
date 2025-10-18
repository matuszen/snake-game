import pygame
import sys
from game import play
dane = [
    (1, 1, 1, 3, 3),
    (2, 1, 1, 3, 3),
    (3, 1, 1, 3, 3),
    (3, 2, 1, 3, 3),
    (3, 3, 1, 7, 7),
    (3, 4, 2, 7, 7),
    (3, 5, 2, 7, 7),
    (3, 6, 2, 7, 7),
    (3, 7, 2, 7, 7),
    (4, 7, 2, 7, 7),
    (5, 7, 2, 7, 7),
    (6, 7, 2, 7, 7),
    (7, 7, 2, 2, 11),
    (7, 8, 3, 2, 11),
    (7, 9, 3, 2, 11),
    (7, 10, 3, 2, 11),
    (7, 11, 3, 2, 11),
    (6, 11, 3, 2, 11),
    (5, 11, 3, 2, 11),
    (4, 11, 3, 2, 11),
    (3, 11, 3, 2, 11),
    (2, 11, 3, 20, 21),
    (2, 12, 4, 20, 21),
    (2, 13, 4, 20, 21),
    (2, 14, 4, 20, 21),
    (2, 15, 4, 20, 21),
    (2, 16, 4, 20, 21),
    (2, 17, 4, 20, 21),
    (2, 18, 4, 20, 21),
    (2, 19, 4, 20, 21),
    (2, 20, 4, 20, 21),
    (2, 21, 4, 20, 21),
    (3, 21, 4, 20, 21),
    (4, 21, 4, 20, 21),
    (5, 21, 4, 20, 21),
    (6, 21, 4, 20, 21),
    (7, 21, 4, 20, 21),
    (8, 21, 4, 20, 21),
    (9, 21, 4, 20, 21),
    (10, 21, 4, 20, 21),
    (11, 21, 4, 20, 21),
    (12, 21, 4, 20, 21),
    (13, 21, 4, 20, 21),
    (14, 21, 4, 20, 21),
    (15, 21, 4, 20, 21),
    (16, 21, 4, 20, 21),
    (17, 21, 4, 20, 21),
    (18, 21, 4, 20, 21),
    (19, 21, 4, 20, 21),
    (20
     , 21, 4, 20, 21),
]


pygame.init()

# --- KONFIGURACJA OKNA ---
WIDTH, HEIGHT = 600, 400
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Menu")

# --- KOLORY ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
GRAY = (70, 70, 70)
HIGHLIGHT = (0, 255, 0)

# --- FONT ---
FONT = pygame.font.SysFont("Arial", 32)

# --- POMOCNICZE FUNKCJE ---

def draw_text(text, y, selected=False):
    """Rysuje tekst w menu"""
    color = HIGHLIGHT if selected else WHITE
    label = FONT.render(text, True, color)
    rect = label.get_rect(center=(WIDTH//2, y))
    SCREEN.blit(label, rect)



def wait_for_key():
    """Czeka aż użytkownik naciśnie klawisz ESC lub ENTER"""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                return event.key

# --- FUNKCJE GRY / SYMULACJI (na razie proste placeholdery) ---


def symulacja_ai():
    play(dane)
    WIDTH, HEIGHT = 600, 400
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
    SCREEN.fill(BLACK)
    draw_text("Symulacja AI w toku...", HEIGHT//2 - 20)
    draw_text("ESC - powrót", HEIGHT//2 + 30)
    pygame.display.flip()
    key = wait_for_key()
    if key == pygame.K_ESCAPE:
        return

def symulacja_algorytmu():
    SCREEN.fill(BLACK)
    draw_text("Symulacja algorytmu w toku...", HEIGHT//2 - 20)
    draw_text("ESC - powrót", HEIGHT//2 + 30)
    pygame.display.flip()
    key = wait_for_key()
    if key == pygame.K_ESCAPE:
        return

def symulacja_oba():
    SCREEN.fill(BLACK)
    draw_text("Symulacja AI i algorytmu", HEIGHT//2 - 20)
    draw_text("ESC - powrót", HEIGHT//2 + 30)
    pygame.display.flip()
    key = wait_for_key()
    if key == pygame.K_ESCAPE:
        return

# --- PODMENU SYMULACJI ---

def menu_symulacji():
    options = ["Symulacja AI", "Symulacja algorytmu", "Obie symulacje", "Powrót"]
    selected = 0

    while True:
        SCREEN.fill(BLACK)
        draw_text("== MENU SYMULACJI ==", 80)
        for i, opt in enumerate(options):
            draw_text(opt, 150 + i * 50, selected == i)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if selected == 0:
                        symulacja_ai()
                    elif selected == 1:
                        symulacja_algorytmu()
                    elif selected == 2:
                        symulacja_oba()
                    elif selected == 3:
                        return
                elif event.key == pygame.K_ESCAPE:
                    return

# --- MENU GŁÓWNE ---

def menu_glowne():
    options = ["Przeprowadź symulację", "Wyjdź"]
    selected = 0

    while True:
        SCREEN.fill(BLACK)
        draw_text("== MENU GŁÓWNE ==", 80)
        for i, opt in enumerate(options):
            draw_text(opt, 150 + i * 60, selected == i)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if selected == 0:
                        menu_symulacji()
                    elif selected == 1:
                        pygame.quit()
                        sys.exit()

# --- START ---
menu_glowne()
