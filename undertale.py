import sys
import math
import random
import pygame

# --- INITIALISATION & WINDOW CONFIG ---
pygame.init()
pygame.font.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Undertale Bullet Hell Engine")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Courier New", 24, bold=True)

# --- COLORS ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

# --- BATTLE BOX DIMENSIONS ---
BOX_LEFT = 250
BOX_TOP = 250
BOX_WIDTH = 300
BOX_HEIGHT = 200

# --- GAME STATES & VARIABLES ---
player_hp = 20
player_max_hp = 20
player_x = BOX_LEFT + BOX_WIDTH // 2
player_y = BOX_TOP + BOX_HEIGHT // 2
player_radius = 8
player_speed = 4
invincibility_frames = 0

monster_hp = 100
monster_max_hp = 100

game_state = "PLAYER_TURN"  # PLAYER_TURN, MONSTER_TURN, GAME_OVER, VICTORY
menu_options = ["FIGHT", "ACT", "ITEM", "MERCY"]
selected_option = 0

turn_timer = 0
bullets = pygame.sprite.Group()


# --- BULLET PATTERN CLASSES ---
class Bullet(pygame.sprite.Sprite):
    """Base class for all Undertale obstacles."""

    def __init__(self, x, y, dx, dy, bullet_type="bone"):
        super().__init__()
        self.type = bullet_type
        self.dx = dx
        self.dy = dy

        if self.type == "bone":
            self.image = pygame.Surface((12, 60))
            self.image.fill(WHITE)
            self.rect = self.image.get_rect(midbottom=(x, y))
        elif self.type == "blaster_beam":
            self.image = pygame.Surface((30, BOX_HEIGHT))
            self.image.fill(WHITE)
            self.rect = self.image.get_rect(topleft=(x, y))
        elif self.type == "circle":
            self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(self.image, WHITE, (8, 8), 8)
            self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

        if (
            self.rect.right < 0
            or self.rect.left > SCREEN_WIDTH
            or self.rect.bottom < 0
            or self.rect.top > SCREEN_HEIGHT
        ):
            self.kill()


# --- BULLET PATTERN GENERATORS ---
def spawn_bone_wall(frame):
    """Pattern 1: Traditional scrolling bone hazard."""
    if frame % 25 == 0:
        bullets.add(Bullet(BOX_LEFT + BOX_WIDTH, BOX_TOP + BOX_HEIGHT - 2, -4, 0, "bone"))


def spawn_gaster_blaster(frame):
    """Pattern 2: Telegraphed column beams."""
    if frame == 30:
        bullets.add(Bullet(BOX_LEFT + 60, BOX_TOP, 0, 0, "blaster_beam"))
    if frame == 100:
        bullets.add(Bullet(BOX_LEFT + 180, BOX_TOP, 0, 0, "blaster_beam"))


def spawn_aimed_circles(frame):
    """Pattern 3: Rings tracking the player's core layout location."""
    if frame % 40 == 0:
        angle = math.atan2(player_y - BOX_TOP, player_x - (BOX_LEFT + BOX_WIDTH // 2))
        dx = math.cos(angle) * 3
        dy = math.sin(angle) * 3
        bullets.add(Bullet(BOX_LEFT + BOX_WIDTH // 2, BOX_TOP, dx, dy, "circle"))


# --- MAIN ENGINE LOOPS ---
running = True
current_pattern = 1

while running:
    clock.tick(60)
    screen.fill(BLACK)

    # --- EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "PLAYER_TURN" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                selected_option = (selected_option - 1) % 4
            elif event.key == pygame.K_RIGHT:
                selected_option = (selected_option + 1) % 4
            elif event.key == pygame.K_z:  # Confirm Action
                if selected_option == 0:  # FIGHT
                    monster_hp = max(0, monster_hp - random.randint(15, 25))
                elif selected_option == 2:  # ITEM
                    player_hp = min(player_max_hp, player_hp + 10)

                if monster_hp <= 0:
                    game_state = "VICTORY"
                else:
                    game_state = "MONSTER_TURN"
                    turn_timer = 0
                    current_pattern = random.choice([1, 2, 3])  # Fixed broken reference
                    player_x = BOX_LEFT + BOX_WIDTH // 2
                    player_y = BOX_TOP + BOX_HEIGHT // 2

    # --- REAL-TIME SOUL GAMEPLAY (MONSTER TURN) ---
    if game_state == "MONSTER_TURN":
        turn_timer += 1

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_RIGHT]:
            player_x += player_speed
        if keys[pygame.K_UP]:
            player_y -= player_speed
        if keys[pygame.K_DOWN]:
            player_y += player_speed

        player_x = max(
            BOX_LEFT + player_radius + 4, min(player_x, BOX_LEFT + BOX_WIDTH - player_radius - 4)
        )
        player_y = max(
            BOX_TOP + player_radius + 4, min(player_y, BOX_TOP + BOX_HEIGHT - player_radius - 4)
        )

        if current_pattern == 1:
            spawn_bone_wall(turn_timer)
        elif current_pattern == 2:
            spawn_gaster_blaster(turn_timer)
        elif current_pattern == 3:
            spawn_aimed_circles(turn_timer)

        bullets.update()

        if invincibility_frames > 0:
            invincibility_frames -= 1
        else:
            player_rect = pygame.Rect(
                player_x - player_radius,
                player_y - player_radius,
                player_radius * 2,
                player_radius * 2,
            )
            for bullet in bullets:
                if player_rect.colliderect(bullet.rect):
                    player_hp = max(0, player_hp - 4)
                    invincibility_frames = 30
                    if player_hp <= 0:
                        game_state = "GAME_OVER"

        if turn_timer >= 240:
            bullets.empty()
            game_state = "PLAYER_TURN"

    # --- RENDERING ENGINE STAGE ---
    pygame.draw.rect(screen, WHITE, (BOX_LEFT, BOX_TOP, BOX_WIDTH, BOX_HEIGHT), 4)

    if game_state == "PLAYER_TURN":
        for i, option in enumerate(menu_options):
            color = YELLOW if i == selected_option else WHITE
            text_surf = FONT.render(f"[{option}]", True, color)
            screen.blit(text_surf, (70 + (i * 180), 500))

        msg = FONT.render("* Use Arrows to select. Press Z.", True, WHITE)
        screen.blit(msg, (BOX_LEFT - 30, BOX_TOP + 60))

    elif game_state == "MONSTER_TURN":
        bullets.draw(screen)
        if invincibility_frames % 4 < 2:
            pygame.draw.circle(screen, RED, (int(player_x), int(player_y)), player_radius)

    monster_text = FONT.render(f"ENEMY HP: {monster_hp}/{monster_max_hp}", True, WHITE)
    screen.blit(monster_text, (BOX_LEFT, 50))

    hp_text = FONT.render(f"YOUR HP: {player_hp}/{player_max_hp}", True, YELLOW)
    screen.blit(hp_text, (BOX_LEFT, 120))

    if game_state == "GAME_OVER":
        screen.fill(BLACK)
        lost_text = FONT.render("GAME OVER - Stay determined...", True, RED)
        screen.blit(lost_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2))
    elif game_state == "VICTORY":
        screen.fill(BLACK)
        win_text = FONT.render("YOU WIN! You earned 0 EXP.", True, GREEN)
        screen.blit(win_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))

    pygame.display.flip()

pygame.quit()
sys.exit()
