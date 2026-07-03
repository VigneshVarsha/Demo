import pygame
import random

def start_game(level):
    # Initialize Pygame
    # We do a basic check so tests that might mock init don't crash
    if not pygame.get_init():
        pygame.init()

    # Screen dimensions
    WIDTH, HEIGHT = 800, 600
    # Allow test runners to mock display
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(f"Little Fighter - Level {level}")
        has_display = True
    except pygame.error:
        # headless environment fallback
        screen = pygame.Surface((WIDTH, HEIGHT))
        has_display = False

    clock = pygame.time.Clock()

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)

    # Player properties
    player_size = 50
    player_x = WIDTH // 2 - player_size // 2
    player_y = HEIGHT - player_size - 20
    player_speed = 5

    # Projectile properties
    projectiles = []
    projectile_speed = 7
    projectile_size = 5

    # Enemy properties
    enemies = []
    enemy_size = 40
    # Higher level means faster enemies and more frequent spawns
    enemy_speed = 2 + (level * 0.5)
    spawn_rate = max(10, 60 - (level * 5))
    frame_count = 0

    score = 0
    font = pygame.font.SysFont(None, 36) if pygame.font.get_init() else None

    running = True

    # To prevent infinite loops in test environments, cap frames if there's no display
    frames_run = 0
    max_test_frames = 100

    while running:
        screen.fill(BLACK)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    projectiles.append([player_x + player_size // 2 - projectile_size // 2, player_y])
                elif event.key == pygame.K_ESCAPE:
                    running = False

        # Key handling for continuous movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < WIDTH - player_size:
            player_x += player_speed
        if keys[pygame.K_UP] and player_y > 0:
            player_y -= player_speed
        if keys[pygame.K_DOWN] and player_y < HEIGHT - player_size:
            player_y += player_speed

        # Spawn enemies
        frame_count += 1
        if frame_count % int(spawn_rate) == 0:
            enemy_x = random.randint(0, WIDTH - enemy_size)
            enemies.append([enemy_x, -enemy_size])

        # Update projectiles
        for p in projectiles[:]:
            p[1] -= projectile_speed
            if p[1] < 0:
                projectiles.remove(p)

        # Update enemies
        for e in enemies[:]:
            e[1] += enemy_speed
            if e[1] > HEIGHT:
                enemies.remove(e)

        # Collision detection (Projectiles hitting enemies)
        for p in projectiles[:]:
            for e in enemies[:]:
                p_rect = pygame.Rect(p[0], p[1], projectile_size, projectile_size * 2)
                e_rect = pygame.Rect(e[0], e[1], enemy_size, enemy_size)
                if p_rect.colliderect(e_rect):
                    if p in projectiles:
                        projectiles.remove(p)
                    if e in enemies:
                        enemies.remove(e)
                    score += 10
                    break

        # Collision detection (Enemies hitting player)
        player_rect = pygame.Rect(player_x, player_y, player_size, player_size)
        for e in enemies:
            e_rect = pygame.Rect(e[0], e[1], enemy_size, enemy_size)
            if player_rect.colliderect(e_rect):
                running = False # Game Over

        # Draw player
        pygame.draw.rect(screen, BLUE, (player_x, player_y, player_size, player_size))

        # Draw enemies
        for e in enemies:
            pygame.draw.rect(screen, RED, (e[0], e[1], enemy_size, enemy_size))

        # Draw projectiles
        for p in projectiles:
            pygame.draw.rect(screen, YELLOW, (p[0], p[1], projectile_size, projectile_size * 2))

        # Draw score and level
        if font:
            score_text = font.render(f"Score: {score}", True, WHITE)
            level_text = font.render(f"Level: {level}", True, WHITE)
            screen.blit(score_text, (10, 10))
            screen.blit(level_text, (10, 40))

        if has_display:
            pygame.display.flip()
            clock.tick(60)
        else:
            frames_run += 1
            if frames_run > max_test_frames:
                running = False

    pygame.quit()

if __name__ == "__main__":
    # Start at level 1 if run directly
    start_game(1)
