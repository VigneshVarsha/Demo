import pygame, random, sys, time

# --- Init ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Super Graphics Shooter: Power-Up Edition")
font = pygame.font.SysFont(None, 36)

# --- Helper: safe image loader ---
def load_image(name, size=(50, 50), fill_color=(120, 120, 120)):
    try:
        return pygame.image.load(name).convert_alpha()
    except:
        surf = pygame.Surface(size)
        surf.fill(fill_color)
        print(f"[Warning] Missing image: {name}")
        return surf

# --- Assets ---
player_img = load_image("player.png")
enemy_img = load_image("enemy.png")
bullet_img = load_image("bullet.png")
bullet2_img = load_image("Bullet2.png")  # Boss bullets
boss_img = load_image("boss.png", (180, 100))
background_img = load_image("background.png", (WIDTH, HEIGHT))

triple_icon = load_image("triple_shot.png", (30, 30))
shield_icon = load_image("shield.png", (30, 30))

# --- Classes ---
class Player:
    def __init__(self):
        self.image = player_img
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 70))
        self.speed = 6
        self.triple_shot_active = False
        self.triple_shot_end = 0
        self.shield_active = False
        self.shield_end = 0

    def move(self, keys):
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed

    def shoot(self):
        shots = []
        if self.triple_shot_active:
            shots.append(Bullet(self.rect.centerx, self.rect.top, dx=-4))
            shots.append(Bullet(self.rect.centerx, self.rect.top))
            shots.append(Bullet(self.rect.centerx, self.rect.top, dx=4))
        else:
            shots.append(Bullet(self.rect.centerx, self.rect.top))
        return shots

    def update_powerups(self):
        now = time.time()
        if self.triple_shot_active and now > self.triple_shot_end:
            self.triple_shot_active = False
        if self.shield_active and now > self.shield_end:
            self.shield_active = False

    def draw(self):
        screen.blit(self.image, self.rect)
        if self.shield_active:
            pygame.draw.circle(screen, (0, 150, 255), self.rect.center, self.rect.width, 3)


class Bullet:
    def __init__(self, x, y, dx=0):
        self.image = bullet_img
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 10
        self.dx = dx

    def update(self):
        self.rect.y -= self.speed
        self.rect.x += self.dx

    def draw(self):
        screen.blit(self.image, self.rect)


class BossBullet:
    def __init__(self, x, y, target_x, target_y, speed=4):
        self.image = bullet2_img
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        
        # Calculate direction towards target
        dx = target_x - x
        dy = target_y - y
        distance = max(1, (dx ** 2 + dy ** 2) ** 0.5)  # Avoid division by zero
        self.dx = (dx / distance) * speed
        self.dy = (dy / distance) * speed

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

    def draw(self):
        screen.blit(self.image, self.rect)


class Enemy:
    def __init__(self, speed):
        x = random.randint(0, WIDTH - enemy_img.get_width())
        y = random.randint(-120, -60)
        self.image = enemy_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed

    def update(self):
        self.rect.y += self.speed

    def draw(self):
        screen.blit(self.image, self.rect)


class Boss:
    def __init__(self, hp, speed):
        self.image = boss_img
        self.rect = self.image.get_rect(midtop=(WIDTH // 2, 60))
        self.health = hp
        self.max_health = hp
        self.speed = speed
        self.direction = 1
        self.last_shot = time.time()
        self.shoot_delay = 2.0  # Increased delay between shots
        self.attack_pattern = 0
        self.last_pattern_change = time.time()
        self.bullets = []
        self.invulnerable = False
        self.invulnerable_timer = 0

    def update(self, player_rect):
        # Movement
        self.rect.x += self.speed * self.direction
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.direction *= -1

        # Change attack pattern every 6 seconds (increased)
        now = time.time()
        if now - self.last_pattern_change > 6:
            self.attack_pattern = random.randint(0, 2)
            self.last_pattern_change = now

        # Invulnerability flash
        if self.invulnerable:
            if now > self.invulnerable_timer:
                self.invulnerable = False

        # Shooting with longer delays
        if now - self.last_shot > self.shoot_delay:
            self.shoot(player_rect)
            self.last_shot = now

        # Update boss bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if (bullet.rect.top > HEIGHT or bullet.rect.bottom < 0 or 
                bullet.rect.left > WIDTH or bullet.rect.right < 0):
                self.bullets.remove(bullet)

    def shoot(self, player_rect):
        if self.attack_pattern == 0:  # Targeted shots - reduced to 1 bullet
            self.bullets.append(BossBullet(
                self.rect.centerx, self.rect.bottom,
                player_rect.centerx, player_rect.centery,
                speed=3  # Slower bullets
            ))

        elif self.attack_pattern == 1:  # Spread shot - reduced bullets
            angles = [-20, 0, 20]
            for angle in angles:
                target_x = self.rect.centerx + 200 * (angle / 30)
                target_y = HEIGHT
                self.bullets.append(BossBullet(
                    self.rect.centerx, self.rect.bottom,
                    target_x, target_y,
                    speed=3
                ))

        else:  # Circular pattern - reduced bullets
            for i in range(6):  # Reduced from 8 to 6
                angle = (i / 6) * 360
                rad = angle * 3.14159 / 180
                target_x = self.rect.centerx + 200 * pygame.math.Vector2(1, 0).rotate(angle).x
                target_y = self.rect.centery + 200 * pygame.math.Vector2(1, 0).rotate(angle).y
                self.bullets.append(BossBullet(
                    self.rect.centerx, self.rect.centery,
                    target_x, target_y, speed=3  # Slower bullets
                ))

    def take_damage(self):
        if not self.invulnerable:
            self.health -= 1
            self.invulnerable = True
            self.invulnerable_timer = time.time() + 0.3  # Brief invulnerability

    def draw(self):
        # Flash when invulnerable
        if not self.invulnerable or int(time.time() * 10) % 2 == 0:
            screen.blit(self.image, self.rect)
        
        # Draw health bar
        bar_width = 200
        bar_height = 20
        bar_x = WIDTH // 2 - bar_width // 2
        bar_y = 10
        
        # Background (red)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Health (green)
        health_width = (self.health / self.max_health) * bar_width
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))
        # Border
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

        # Draw boss bullets
        for bullet in self.bullets:
            bullet.draw()


class PowerUp:
    TYPES = ["triple", "shield"]

    def __init__(self, x, y):
        self.type = random.choice(PowerUp.TYPES)
        self.image = triple_icon if self.type == "triple" else shield_icon
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 3
        self.angle = 0

    def update(self):
        self.rect.y += self.speed
        self.angle = (self.angle + 4) % 360

    def draw(self):
        rotated = pygame.transform.rotate(self.image, self.angle)
        rect = rotated.get_rect(center=self.rect.center)
        screen.blit(rotated, rect)


# --- Helpers ---
def draw_text(txt, color, x, y, center=False):
    surf = font.render(txt, True, color)
    rect = surf.get_rect(center=(x, y)) if center else (x, y)
    screen.blit(surf, rect)


def next_stage():
    global stage, stage_cleared, enemies, bullets, boss, boss_defeated
    stage += 1
    enemies.clear()
    bullets.clear()
    powerups.clear()
    boss = None
    boss_defeated = False
    stage_cleared = True


def reset_game():
    global score, stage, enemies, bullets, powerups, boss, boss_defeated, game_over, stage_cleared
    score, stage = 0, 1
    enemies.clear()
    bullets.clear()
    powerups.clear()
    boss = None
    boss_defeated = False
    game_over = False
    stage_cleared = False
    player.rect.center = (WIDTH // 2, HEIGHT - 70)
    player.triple_shot_active = player.shield_active = False


# --- Stage Data ---
STAGE_DATA = {
    1: {"enemy_speed": 3, "wave_size": 6, "boss": None, "score_threshold": 20},
    2: {"enemy_speed": 4, "wave_size": 8, "boss": (8, 3), "score_threshold": 50},  # Reduced boss HP
    3: {"enemy_speed": 5, "wave_size": 10, "boss": (15, 4), "score_threshold": 100},  # Reduced boss HP
    4: {"enemy_speed": 6, "wave_size": 12, "boss": (25, 5), "score_threshold": 200},  # Reduced boss HP
    5: {"enemy_speed": 7, "wave_size": 15, "boss": (35, 6), "score_threshold": None},  # Reduced boss HP
}

# --- Game State ---
clock = pygame.time.Clock()
player = Player()
bullets, enemies, powerups = [], [], []
score, stage = 0, 1
boss = None
boss_defeated = False
game_over = False
stage_cleared = False

# --- Main Loop ---
running = True
while running:
    screen.blit(background_img, (0, 0))
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if not game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            bullets.extend(player.shoot())
        if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            reset_game()

    # Stage transition banner
    if stage_cleared:
        draw_text(f"STAGE {stage}", (0, 255, 0), WIDTH // 2, HEIGHT // 2, center=True)
        pygame.display.update()
        pygame.time.wait(1500)
        stage_cleared = False

    if not game_over:
        player.move(keys)
        player.update_powerups()
        player.draw()

        # Bullets
        for b in bullets[:]:
            b.update()
            if b.rect.bottom < 0:
                bullets.remove(b)
            else:
                b.draw()

        # Enemies
        data = STAGE_DATA.get(stage)
        if data and random.randint(1, 40) == 1 and len(enemies) < data["wave_size"]:
            enemies.append(Enemy(data["enemy_speed"]))

        for e in enemies[:]:
            e.update()
            e.draw()
            if e.rect.top > HEIGHT:
                enemies.remove(e)
            elif e.rect.colliderect(player.rect):
                if not player.shield_active:
                    game_over = True
            else:
                for b in bullets[:]:
                    if e.rect.colliderect(b.rect):
                        enemies.remove(e)
                        bullets.remove(b)
                        score += 1
                        if random.random() < 0.15:  # Increased power-up chance
                            powerups.append(PowerUp(e.rect.centerx, e.rect.centery))
                        break

        # Power-ups
        for p in powerups[:]:
            p.update()
            p.draw()
            if p.rect.top > HEIGHT:
                powerups.remove(p)
            elif p.rect.colliderect(player.rect):
                if p.type == "triple":
                    player.triple_shot_active = True
                    player.triple_shot_end = time.time() + 12  # Longer duration
                elif p.type == "shield":
                    player.shield_active = True
                    player.shield_end = time.time() + 10  # Longer duration
                powerups.remove(p)

        # Boss activation - more frequent for practice
        if data["boss"] and boss is None and random.randint(1, 80) == 1:
            boss = Boss(*data["boss"])

        # Boss behavior
        if boss:
            boss.update(player.rect)
            boss.draw()
            
            # Check collision with boss bullets
            for b in boss.bullets[:]:
                if b.rect.colliderect(player.rect):
                    if not player.shield_active:
                        game_over = True
                    boss.bullets.remove(b)
            
            # Check player bullets hitting boss
            for b in bullets[:]:
                if boss.rect.colliderect(b.rect) and not boss.invulnerable:
                    boss.take_damage()
                    bullets.remove(b)
                    score += 2  # Extra points for hitting boss
                    
            if boss.health <= 0 and not boss_defeated:
                boss_defeated = True
                boss = None
                score += 30  # Big bonus for defeating boss
                # Spawn bonus power-ups when boss is defeated
                for _ in range(3):
                    powerups.append(PowerUp(
                        random.randint(50, WIDTH-50),
                        random.randint(100, HEIGHT//2)
                    ))

        # Level progression based on score
        if stage < len(STAGE_DATA):
            next_stage_threshold = STAGE_DATA[stage]["score_threshold"]
            if next_stage_threshold is not None and score >= next_stage_threshold:
                next_stage()

        # HUD
        draw_text(f"Score: {score}", (255, 255, 255), 10, 10)
        draw_text(f"Stage: {stage}", (255, 255, 0), WIDTH - 130, 10)
        
        # Show next level requirement if not final stage
        if stage < len(STAGE_DATA):
            next_level_score = STAGE_DATA[stage]["score_threshold"]
            if next_level_score is not None:
                draw_text(f"Next Level: {next_level_score}", (200, 200, 100), WIDTH // 2, 40, center=True)
        
        # Boss warning
        if boss:
            draw_text("BOSS FIGHT!", (255, 50, 50), WIDTH // 2, 70, center=True)
        
        if player.triple_shot_active:
            t = max(0, int(player.triple_shot_end - time.time()))
            draw_text(f"Triple Shot: {t}s", (255, 255, 0), 10, 40)
        if player.shield_active:
            t = max(0, int(player.shield_end - time.time()))
            draw_text(f"Shield: {t}s", (0, 255, 255), 10, 70)

    else:
        draw_text("GAME OVER", (255, 0, 0), WIDTH // 2, HEIGHT // 2 - 20, center=True)
        draw_text("Press R to Restart", (200, 200, 200), WIDTH // 2, HEIGHT // 2 + 20, center=True)
        draw_text(f"Final Score: {score}", (255, 255, 0), WIDTH // 2, HEIGHT // 2 + 60, center=True)

    pygame.display.update()
    clock.tick(60)
pygame.quit()
