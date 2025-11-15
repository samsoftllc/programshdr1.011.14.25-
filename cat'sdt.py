#!/usr/bin/env python3
# Pygame Overworld→Battle→Result demo (single file, no assets)
# - State base + Overworld/Battle/Result subclasses
# - 60 FPS render, fixed 1/60 s update accumulator
# - Dialog box with pygame.font
# - Timed-hit window using pygame.time.get_ticks()
# - Deterministic per-battle RNG via random.Random(seed)

import sys, math, random
import pygame

# -------------------------
# Config
# -------------------------
WIDTH, HEIGHT = 640, 360
FPS = 60
FIXED_DT = 1.0 / 60.0
UI_SCALE = 2
FONT_SIZE = 8 * UI_SCALE
DIALOG_PAD = 8
DIALOG_H = 72
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY  = (40,40,40)
GREEN = (40,200,80)
RED   = (220,60,60)
BLUE  = (60,120,220)
YELLOW= (240,220,60)

# -------------------------
# Utilities
# -------------------------
def draw_dialog(surface, font, lines, color=WHITE):
    box = pygame.Rect(0, HEIGHT - DIALOG_H, WIDTH, DIALOG_H)
    pygame.draw.rect(surface, BLACK, box)
    pygame.draw.rect(surface, WHITE, box, 2)
    y = box.top + DIALOG_PAD
    for line in lines:
        surf = font.render(line, True, color)
        surface.blit(surf, (DIALOG_PAD, y))
        y += surf.get_height() + 4

# -------------------------
# State system
# -------------------------
class State:
    def __init__(self, game):
        self.game = game
    def enter(self, **kwargs): pass
    def exit(self): pass
    def handle_event(self, e): pass
    def update(self, dt): pass
    def draw(self, surface): pass

class Overworld(State):
    def __init__(self, game):
        super().__init__(game)
        self.player = pygame.Rect(100, 100, 16*UI_SCALE, 16*UI_SCALE)
        self.speed = 120  # px/s
        self.encounter_zone = pygame.Rect(420, 120, 60, 60)
        self.msg = ["WASD/Arrows to move.", "Step into the blue zone to battle."]
    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
            self.game.push_state("battle", seed=self.game.next_seed())
    def update(self, dt):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:    dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  dy += 1
        if dx or dy:
            inv = 1.0/math.sqrt(dx*dx+dy*dy)
            self.player.x += int(dx*inv*self.speed*dt)
            self.player.y += int(dy*inv*self.speed*dt)
        self.player.clamp_ip(pygame.Rect(0,0,WIDTH,HEIGHT))
        if self.player.colliderect(self.encounter_zone):
            self.game.push_state("battle", seed=self.game.next_seed())
    def draw(self, surface):
        surface.fill((8,12,16))
        # ground
        pygame.draw.rect(surface, (20,30,45), pygame.Rect(0,0,WIDTH,HEIGHT))
        # encounter zone
        pygame.draw.rect(surface, BLUE, self.encounter_zone, border_radius=6)
        # player
        pygame.draw.rect(surface, YELLOW, self.player)
        draw_dialog(surface, self.game.font, self.msg)

class Battle(State):
    def __init__(self, game):
        super().__init__(game)
        self.rng = random.Random(0)
        self.player_hp = 10
        self.enemy_hp = 10
        self.prompt = ["SPACE to attack when the marker", "hits the green window!"]
        # Timed-hit bar
        self.bar = pygame.Rect(80, 140, WIDTH-160, 20)
        self.marker_x = self.bar.left
        self.marker_speed = 320  # px/s
        self.hit_window = (0,0)  # will set per attack
        self.window_flash_ms = 200
        self.window_set_time = 0
        # pacing
        self.state = "ready"   # ready → swinging → result → enemy_turn → ready…
        self.last_result = ""
        self.last_color = WHITE
        self.turn_delay_ms = 500
        self.state_change_t = 0

    def enter(self, **kwargs):
        seed = kwargs.get("seed", 0)
        self.rng = random.Random(seed)
        self._new_turn()

    def _new_turn(self):
        # Set new hit window deterministically
        w = self.rng.randint(30, 60)  # px width
        left = self.rng.randint(self.bar.left+20, self.bar.right-20-w)
        self.hit_window = (left, left + w)
        self.window_set_time = pygame.time.get_ticks()
        self.marker_x = self.bar.left
        self.state = "ready"
        self.last_result = ""

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.game.replace_state("overworld")
        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and self.state == "ready":
            self.state = "swinging"

    def update(self, dt):
        now = pygame.time.get_ticks()
        if self.state == "swinging":
            self.marker_x += self.marker_speed*dt
            if self.marker_x >= self.bar.right:
                self._resolve_player_attack()
        elif self.state == "result":
            if now - self.state_change_t >= self.turn_delay_ms:
                self.state = "enemy_turn"
                self.state_change_t = now
        elif self.state == "enemy_turn":
            if now - self.state_change_t >= self.turn_delay_ms:
                dmg = 1 if self.rng.random() < 0.8 else 2
                self.player_hp = max(0, self.player_hp - dmg)
                self.last_result = f"Enemy hits you for {dmg}!"
                self.last_color = RED
                if self.player_hp <= 0:
                    self.game.replace_state("result", victory=False)
                else:
                    self._new_turn()

    def _resolve_player_attack(self):
        L, R = self.hit_window
        if L <= self.marker_x <= R:
            # closer to center = more damage
            center = (L + R)/2
            dist = abs(self.marker_x - center)
            span = (R - L)/2
            factor = max(0.2, 1.0 - dist/(span+1e-6))
            dmg = 1 + int(2*factor)  # 1..3
            self.enemy_hp = max(0, self.enemy_hp - dmg)
            self.last_result = f"Timed hit! {dmg} dmg."
            self.last_color = GREEN
        else:
            self.last_result = "Miss!"
            self.last_color = WHITE
        if self.enemy_hp <= 0:
            self.game.replace_state("result", victory=True)
            return
        self.state = "result"
        self.state_change_t = pygame.time.get_ticks()

    def draw(self, surface):
        surface.fill((18,18,28))
        # UI frames
        pygame.draw.rect(surface, WHITE, pygame.Rect(16,16,WIDTH-32,60), 2)
        pygame.draw.rect(surface, WHITE, pygame.Rect(16,96,WIDTH-32,HEIGHT-112), 2)

        # HP
        hp_font = self.game.font
        p = hp_font.render(f"HP: {self.player_hp}", True, YELLOW)
        e = hp_font.render(f"Enemy HP: {self.enemy_hp}", True, RED)
        surface.blit(p, (28, 28))
        surface.blit(e, (WIDTH-28-e.get_width(), 28))

        # Bar + hit window
        pygame.draw.rect(surface, GRAY, self.bar, border_radius=6)
        L, R = self.hit_window
        wrect = pygame.Rect(L, self.bar.top, R-L, self.bar.height)
        # flash window briefly when it changes
        if pygame.time.get_ticks() - self.window_set_time < self.window_flash_ms:
            pygame.draw.rect(surface, (80,255,120), wrect, border_radius=6)
        else:
            pygame.draw.rect(surface, (60,160,100), wrect, border_radius=6)

        # marker
        mx = int(self.marker_x)
        pygame.draw.rect(surface, WHITE, pygame.Rect(mx-2, self.bar.top-6, 4, self.bar.height+12))

        # prompt / result
        lines = self.prompt[:] if self.state in ("ready","swinging") else [self.last_result]
        draw_dialog(surface, self.game.font, lines, self.last_color)

class Result(State):
    def __init__(self, game):
        super().__init__(game)
        self.victory = True
        self.msg = []
        self.cooldown_ms = 600
        self.enter_t = 0
    def enter(self, **kwargs):
        self.victory = kwargs.get("victory", True)
        self.msg = (["Victory!", "Press SPACE to return."] if self.victory
                    else ["Defeat…", "Press SPACE to return."])
        self.enter_t = pygame.time.get_ticks()
    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
            self.game.replace_state("overworld")
    def draw(self, surface):
        surface.fill((12,10,18))
        t = "YOU WIN!" if self.victory else "YOU LOSE…"
        big = self.game.big_font.render(t, True, WHITE)
        surface.blit(big, (WIDTH//2 - big.get_width()//2, HEIGHT//3 - big.get_height()//2))
        draw_dialog(surface, self.game.font, self.msg)

# -------------------------
# Game wrapper
# -------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Overworld → Battle → Result (Pygame)")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier New, Consolas, Monospace", FONT_SIZE)
        self.big_font = pygame.font.SysFont("Courier New, Consolas, Monospace", FONT_SIZE*2)
        self.states = {
            "overworld": Overworld(self),
            "battle": Battle(self),
            "result": Result(self),
        }
        self.stack = []
        self._seed_counter = 1
        self.push_state("overworld")

    def next_seed(self):
        # Simple deterministic series for reproducible play sessions
        s = self._seed_counter
        self._seed_counter += 1
        return s

    def current(self):
        return self.stack[-1] if self.stack else None

    def push_state(self, name, **kwargs):
        st = self.states[name]
        self.stack.append(st)
        st.enter(**kwargs)

    def replace_state(self, name, **kwargs):
        if self.stack:
            self.stack.pop().exit()
        self.push_state(name, **kwargs)

    def run(self):
        running = True
        accumulator = 0.0
        prev_ticks = pygame.time.get_ticks()

        while running:
            # --- events ---
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_q:
                    running = False
                else:
                    cur = self.current()
                    if cur: cur.handle_event(e)

            # --- fixed timestep update ---
            now_ticks = pygame.time.get_ticks()
            frame_dt = (now_ticks - prev_ticks) / 1000.0
            prev_ticks = now_ticks
            accumulator += frame_dt
            # Cap to avoid spiral of death if paused
            accumulator = min(accumulator, 0.25)

            while accumulator >= FIXED_DT:
                cur = self.current()
                if cur: cur.update(FIXED_DT)
                accumulator -= FIXED_DT

            # --- render ---
            cur = self.current()
            if cur: cur.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit(0)

if __name__ == "__main__":
    Game().run()
