import pygame
import sys
from stats import wykresy


    
def play(dane):

    CELL_SIZE = 20
    GRID_WIDTH = 100
    GRID_HEIGHT = 50
    WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
    WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE

    SNAKE_COLOR = (0, 200, 0)
    HEAD_COLOR = (0, 255, 0)
    FOOD_COLOR = (255, 0, 0)
    BG_COLOR = (30, 30, 30)
    TEXT_COLOR = (255, 255, 255)

    FPS = 5 



    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Symulacja Snake")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 28, bold=True)


    def draw_cell(x, y, color):
        rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, color, rect)


    def draw_food(x, y, frame_count):
        radius = CELL_SIZE // 2 + (frame_count % 6)  
        center = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)
        pygame.draw.circle(screen, FOOD_COLOR, center, radius)


    def show_end_screen(final_length):
        frame_count = 0
        waiting = True
        while waiting:
            screen.fill(BG_COLOR)
            color = (255, 100 + (frame_count % 155), 100)
            text1 = font.render("KONIEC GRY!", True, color)
            text2 = font.render(f"Wynik: {final_length}", True, TEXT_COLOR)
            text3 = font.render("Naciśnij ESC lub zamknij okno", True, (180, 180, 180))
            screen.blit(text1, (WINDOW_WIDTH//2 - text1.get_width()//2, WINDOW_HEIGHT//2 - 60))
            screen.blit(text2, (WINDOW_WIDTH//2 - text2.get_width()//2, WINDOW_HEIGHT//2))
            screen.blit(text3, (WINDOW_WIDTH//2 - text3.get_width()//2, WINDOW_HEIGHT//2 + 60))
            pygame.display.flip()
            clock.tick(10)
            frame_count += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    waiting = False


    def draw_background(frame_count):
        screen.fill(BG_COLOR)
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
                shade = 20 + (frame_count + x + y) % 30  
                pygame.draw.rect(screen, (shade, shade, shade), (x, y, CELL_SIZE, CELL_SIZE))


    def simulate_snake():
        frame_index = 0
        snake_positions = []
        for frame in dane:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            x_head, y_head, length, food_x, food_y = frame
      
            screen.fill(BG_COLOR)

            draw_background(frame_index)
            
            x_head, y_head, length, food_x, food_y = frame

            snake_positions.insert(0, (x_head, y_head))    
            snake_positions = snake_positions[:length]      

            screen.fill(BG_COLOR)
            for pos in snake_positions[1:]:
                draw_cell(pos[0], pos[1], SNAKE_COLOR)       
            draw_cell(snake_positions[0][0], snake_positions[0][1], HEAD_COLOR)  

            draw_food(food_x, food_y, frame_index)
            
            pygame.display.flip()
            clock.tick(FPS)
            frame_index += 1

        final_length = dane[-1][2]
        show_end_screen(final_length)
        
    simulate_snake()
    wykresy(dane)



    
