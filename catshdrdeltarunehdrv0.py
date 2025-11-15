#!/usr/bin/env python3
# Pygame Overworld→Battle→Result demo (single file, no assets)
# Merged with Deltarune Ch1+Ch2 simulation concepts.
# - State base + MainMenu/Overworld(s)/Battle/Result subclasses
# - 60 FPS render, fixed 1/60 s update accumulator
# - Dialog box with pygame.font
# - Battle:
#   - Player Turn: Timed-hit window (from original demo)
#   - Enemy Turn: Bullet-hell dodging phase (simulated with math)
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

# Colors
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (40,40,40)
GREEN = (40,200,80)
RED = (220,60,60)
BLUE = (60,120,220)
YELLOW= (240,220,60)
PURPLE = (180,60,220)
CYAN = (60,220,220)

# -------------------------
# Utilities
# -------------------------

def draw_dialog(surface, font, lines, color=WHITE):
    """Draws the dialog box at the bottom of the screen."""
    box = pygame.Rect(0, HEIGHT - DIALOG_H, WIDTH, DIALOG_H)
    pygame.draw.rect(surface, BLACK, box)
    pygame.draw.rect(surface, WHITE, box, 2, border_radius=4)
    y = box.top + DIALOG_PAD
    for line in lines:
        surf = font.render(line, True, color)
        surface.blit(surf, (DIALOG_PAD + 4, y))
        y += surf.get_height() + 4

def draw_heart(surface, center_pos, size=12, color=RED):
    """Draws the player 'soul' (a simple heart/diamond shape)."""
    x, y = center_pos
    s = size / 2
    # Simple polygon for the heart/soul
    pygame.draw.polygon(surface, color, [
        (x, y - s), (x - s, y), (x, y + s), (x + s, y)
    ])

# -------------------------
# State system
# -------------------------

class State:
    """Base class for all game states (menu, overworld, battle)."""
    def __init__(self, game):
        self.game = game
    def enter(self, **kwargs):
        pass
    def exit(self):
        pass
    def handle_event(self, e):
        pass
    def update(self, dt):
        pass
    def draw(self, surface):
        pass

class MainMenu(State):
    """The first screen the player sees."""
    def __init__(self, game):
        super().__init__(game)
        self.msg = [
            "CAT'S DELTARUNE ENGINE 0.2",
            "",
            "Press [SPACE] to Start",
            "Press [Q] or [ESC] to Quit"
        ]

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                # Start Chapter 1
                self.game.chapter = 1
                self.game.replace_state("overworld_ch1")
            elif e.key == pygame.K_ESCAPE or e.key == pygame.K_q:
                self.game.running = False

    def draw(self, surface):
        surface.fill(BLACK)
        # Draw title and prompts
        y = HEIGHT // 3
        for i, line in enumerate(self.msg):
            font = self.game.big_font if i == 0 else self.game.font
            color = YELLOW if i == 0 else WHITE
            surf = font.render(line, True, color)
            x = WIDTH // 2 - surf.get_width() // 2
            surface.blit(surf, (x, y))
            y += surf.get_height() + 12

class Overworld(State):
    """Base class for overworld states, handles player movement."""
    def __init__(self, game):
        super().__init__(game)
        self.player = pygame.Rect(100, 100, 16 * UI_SCALE, 16 * UI_SCALE)
        self.speed = 120 # px/s
        self.encounter_zones = [] # List of tuples: (rect, battle_params_dict)
        self.msg = ["WASD/Arrows to move.", "Step into the blue zones to battle."]

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.game.replace_state("main_menu")

    def update(self, dt):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1

        if dx or dy:
            inv = 1.0 / math.sqrt(dx*dx + dy*dy)
            self.player.x += int(dx * inv * self.speed * dt)
            self.player.y += int(dy * inv * self.speed * dt)
            self.player.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT - DIALOG_H))

        # Check for battle encounters
        for zone, params in self.encounter_zones:
            if self.player.colliderect(zone):
                # Add a seed to the battle parameters
                params_with_seed = params.copy()
                params_with_seed["seed"] = self.game.next_seed()
                self.game.push_state("battle", **params_with_seed)
                # Nudge player out to prevent re-triggering
                self.player.x -= 20

    def draw(self, surface):
        # Ground color (overridden by subclasses)
        surface.fill((8, 12, 16))
        # Draw encounter zones
        for zone, _ in self.encounter_zones:
            pygame.draw.rect(surface, BLUE, zone, border_radius=6)
        # Draw player
        pygame.draw.rect(surface, YELLOW, self.player)
        # Draw dialog
        draw_dialog(surface, self.game.font, self.msg)

class Overworld_Ch1(Overworld):
    """Chapter 1: Dark World Field"""
    def __init__(self, game):
        super().__init__(game)
        self.msg = ["Chapter 1: The Dark World.", "Find the 'Boss' zone."]
        self.encounter_zones = [
            # Zone rect, battle_params
            (pygame.Rect(220, 150, 60, 60), {"enemy_name": "Lancer", "is_boss": False}),
            (pygame.Rect(420, 120, 60, 60), {"enemy_name": "King", "is_boss": True})
        ]

    def draw(self, surface):
        surface.fill((8, 12, 16)) # Dark world color
        super().draw(surface)

class Overworld_Ch2(Overworld):
    """Chapter 2: Cyber World"""
    def __init__(self, game):
        super().__init__(game)
        self.msg = ["Chapter 2: The Cyber World.", "Find the 'Queen' zone."]
        self.encounter_zones = [
            (pygame.Rect(180, 200, 60, 60), {"enemy_name": "Spamton", "is_boss": False}),
            (pygame.Rect(500, 100, 60, 60), {"enemy_name": "Queen", "is_boss": True})
        ]

    def draw(self, surface):
        surface.fill((20, 0, 30)) # Cyber world color
        super().draw(surface)

class Battle(State):
    """Handles both timed-hit attacks and bullet-hell dodging."""
    def __init__(self, game):
        super().__init__(game)
        self.rng = random.Random(0)
        
        # Stats
        self.player_hp = 100
        self.enemy_hp = 10
        self.enemy_name = "Enemy"
        self.is_boss = False

        # Player Turn: Timed-hit bar
        self.bar = pygame.Rect(WIDTH // 2 - 120, 140, 240, 20)
        self.marker_x = self.bar.left
        self.marker_speed = 320 # px/s
        self.hit_window = (0, 0)
        self.window_flash_ms = 200
        self.window_set_time = 0

        # Enemy Turn: Dodging
        self.arena = pygame.Rect(WIDTH//2 - 100, 100, 200, 160)
        self.soul = pygame.Rect(0, 0, 12, 12)
        self.soul_speed = 150 # px/s
        self.bullets = [] # List of {'pos': [x, y], 'vel': [vx, vy]}
        self.bullet_timer = 0.0

        # Pacing
        self.state = "player_turn" # player_turn → enemy_turn → player_turn...
        self.substate = "menu"     # Player turn: menu → swinging
        self.turn_delay_ms = 1000  # Pause between turns/results
        self.enemy_turn_duration = 5000 # 5 seconds of dodging
        self.state_change_t = 0
        
        # Dialog
        self.prompt = [""]
        self.last_result = ""
        self.last_color = WHITE

    def enter(self, **kwargs):
        seed = kwargs.get("seed", 0)
        self.enemy_name = kwargs.get("enemy_name", "Enemy")
        self.is_boss = kwargs.get("is_boss", False)
        
        self.rng = random.Random(seed)
        self.enemy_hp = 200 if self.is_boss else 80
        # self.player_hp = 100 # Don't reset player HP
        
        self._new_player_turn()

    def _new_player_turn(self):
        """Resets state for the start of the player's turn."""
        self.state = "player_turn"
        self.substate = "menu"
        self.prompt = [
            f"It's your turn! (Enemy: {self.enemy_name})",
            "SPACE to FIGHT. Z to ACT (Mercy)."
        ]
        self.last_result = ""

    def _setup_timed_hit(self):
        """Sets a new random hit window for the attack bar."""
        w = self.rng.randint(30, 60) # px width
        left = self.rng.randint(self.bar.left + 20, self.bar.right - 20 - w)
        self.hit_window = (left, left + w)
        self.window_set_time = pygame.time.get_ticks()
        self.marker_x = self.bar.left
        self.substate = "swinging"
        self.prompt = [f"Attack {self.enemy_name}!", "Press SPACE in the green window!"]

    def _resolve_player_attack(self):
        """Calculates damage based on the timed hit."""
        L, R = self.hit_window
        dmg = 0
        if L <= self.marker_x <= R:
            # Closer to center = more damage
            center = (L + R) / 2
            dist = abs(self.marker_x - center)
            span = (R - L) / 2
            factor = max(0.2, 1.0 - dist / (span + 1e-6))
            dmg = 10 + int(20 * factor) # 10..30 dmg
            self.enemy_hp = max(0, self.enemy_hp - dmg)
            self.last_result = f"Timed hit! {dmg} dmg."
            self.last_color = GREEN
        else:
            self.last_result = "Miss!"
            self.last_color = WHITE

        self.substate = "result" # Show result for a moment
        self.state_change_t = pygame.time.get_ticks()

    def _start_enemy_turn(self):
        """Transitions to the dodging phase."""
        if self.enemy_hp <= 0:
            # Enemy defeated
            self.game.replace_state("result", victory=True)
            return

        self.state = "enemy_turn"
        self.state_change_t = pygame.time.get_ticks()
        self.bullets = []
        self.bullet_timer = 0.0
        self.soul.center = self.arena.center
        self.prompt = [f"{self.enemy_name} attacks!", "Dodge the bullets!"]

    def _spawn_bullets(self, dt):
        """Generates bullet patterns based on math."""
        self.bullet_timer += dt
        if self.bullet_timer < 0.1: # Spawn rate
            return
        
        self.bullet_timer = 0.0
        t = (pygame.time.get_ticks() - self.state_change_t) / 1000.0
        
        # Simple pattern: spiral
        if "Spamton" in self.enemy_name or "King" in self.enemy_name:
            num_bullets = 2
            for i in range(num_bullets):
                angle = t * 2.0 + (math.pi * 2 * i / num_bullets)
                speed = 80
                vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.bullets.append({
                    'pos': [self.arena.centerx, self.arena.centery], 
                    'vel': vel
                })
        
        # Simple pattern: rain
        elif "Lancer" in self.enemy_name or "Queen" in self.enemy_name:
            x = self.rng.randint(self.arena.left, self.arena.right)
            self.bullets.append({
                'pos': [x, self.arena.top],
                'vel': [0, 100] # Downward velocity
            })

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.game.pop_state() # Return to overworld

        if self.state == "player_turn":
            if self.substate == "menu" and e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE: # FIGHT
                    self._setup_timed_hit()
                elif e.key == pygame.K_z: # ACT (Mercy)
                    self.last_result = "You chose ACT. Enemy is confused."
                    self.last_color = CYAN
                    self.substate = "result"
                    self.state_change_t = pygame.time.get_ticks()
                    
            elif self.substate == "swinging" and e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    self._resolve_player_attack()

    def update(self, dt):
        now = pygame.time.get_ticks()
        
        if self.state == "player_turn":
            if self.substate == "swinging":
                self.marker_x += self.marker_speed * dt
                if self.marker_x >= self.bar.right:
                    self._resolve_player_attack() # Auto-miss if it goes off
            elif self.substate == "result":
                if now - self.state_change_t >= self.turn_delay_ms:
                    self._start_enemy_turn()

        elif self.state == "enemy_turn":
            # --- Dodging Phase ---
            if now - self.state_change_t >= self.enemy_turn_duration:
                self._new_player_turn() # Turn ends
                return

            # 1. Move Soul
            keys = pygame.key.get_pressed()
            dx = dy = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1

            if dx or dy:
                inv = 1.0 / math.sqrt(dx*dx + dy*dy)
                self.soul.x += int(dx * inv * self.soul_speed * dt)
                self.soul.y += int(dy * inv * self.soul_speed * dt)
                self.soul.clamp_ip(self.arena) # Keep soul in bounds

            # 2. Spawn Bullets
            self._spawn_bullets(dt)

            # 3. Move Bullets & Check Hits
            for b in self.bullets[:]: # Iterate on a copy
                b['pos'][0] += b['vel'][0] * dt
                b['pos'][1] += b['vel'][1] * dt
                
                # Check collision with soul
                bullet_rect = pygame.Rect(b['pos'][0]-2, b['pos'][1]-2, 4, 4)
                if self.soul.colliderect(bullet_rect):
                    self.player_hp = max(0, self.player_hp - 10)
                    self.bullets.remove(b)
                    if self.player_hp <= 0:
                        self.game.replace_state("result", victory=False)
                        return # Exit update
                # Remove if off-screen
                elif not self.arena.colliderect(bullet_rect):
                    self.bullets.remove(b)

    def draw(self, surface):
        surface.fill((18, 18, 28)) # Battle background
        now = pygame.time.get_ticks()

        # --- Draw Enemy (simple rect) ---
        enemy_color = PURPLE if self.is_boss else RED
        pygame.draw.rect(surface, enemy_color, pygame.Rect(WIDTH//2 - 30, 40, 60, 60))

        # --- Draw HP ---
        p_hp = self.game.font.render(f"HP: {self.player_hp}", True, YELLOW)
        e_hp = self.game.font.render(f"{self.enemy_name} HP: {self.enemy_hp}", True, RED)
        surface.blit(p_hp, (28, 28))
        surface.blit(e_hp, (WIDTH - 28 - e_hp.get_width(), 28))

        # --- Draw State-Specific UI ---
        if self.state == "player_turn" and self.substate == "swinging":
            # Draw Timed-hit bar
            pygame.draw.rect(surface, GRAY, self.bar, border_radius=6)
            L, R = self.hit_window
            wrect = pygame.Rect(L, self.bar.top, R - L, self.bar.height)
            
            # Flash window
            if now - self.window_set_time < self.window_flash_ms:
                pygame.draw.rect(surface, (80, 255, 120), wrect, border_radius=6)
            else:
                pygame.draw.rect(surface, (60, 160, 100), wrect, border_radius=6)
            
            # Draw marker
            mx = int(self.marker_x)
            pygame.draw.rect(surface, WHITE, pygame.Rect(mx - 2, self.bar.top - 6, 4, self.bar.height + 12))
        
        elif self.state == "enemy_turn":
            # Draw Dodging Arena
            pygame.draw.rect(surface, WHITE, self.arena, 2, border_radius=4)
            # Draw Soul
            draw_heart(surface, self.soul.center, size=self.soul.width, color=RED)
            # Draw Bullets
            for b in self.bullets:
                pygame.draw.circle(surface, CYAN, (int(b['pos'][0]), int(b['pos'][1])), 4)

        # --- Draw Dialog ---
        lines = self.prompt
        color = WHITE
        if self.substate == "result":
            lines = [self.last_result]
            color = self.last_color
        
        draw_dialog(surface, self.game.font, lines, color)

class Result(State):
    """Win/Loss screen."""
    def __init__(self, game):
        super().__init__(game)
        self.victory = True
        self.msg = []
        self.enter_t = 0
        self.title = ""

    def enter(self, **kwargs):
        self.victory = kwargs.get("victory", True)
        self.enter_t = pygame.time.get_ticks()
        
        if self.victory:
            self.title = "YOU WIN!"
            if self.game.chapter == 1:
                self.msg = ["Victory! Chapter 1 Complete.", "Press SPACE to start Chapter 2."]
            else:
                self.msg = ["Victory! All Chapters Complete.", "Press SPACE to return to Menu."]
        else:
            self.title = "YOU LOSE..."
            self.msg = [f"Defeat... Restarting Chapter {self.game.chapter}.", "Press SPACE to continue."]

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
            if self.victory:
                if self.game.chapter == 1:
                    # Progress to Chapter 2
                    self.game.chapter = 2
                    self.game.replace_state("overworld_ch2")
                else:
                    # Game complete, back to menu
                    self.game.replace_state("main_menu")
            else:
                # Retry current chapter
                self.game.replace_state(f"overworld_ch{self.game.chapter}")

    def draw(self, surface):
        surface.fill((12, 10, 18))
        # Draw Title
        big = self.game.big_font.render(self.title, True, YELLOW if self.victory else RED)
        surface.blit(big, (WIDTH // 2 - big.get_width() // 2, HEIGHT // 3 - big.get_height() // 2))
        # Draw dialog
        draw_dialog(surface, self.game.font, self.msg)

# -------------------------
# Game wrapper
# -------------------------

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Cat's Deltarune Engine 0.2")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier New, Consolas, Monospace", FONT_SIZE)
        self.big_font = pygame.font.SysFont("Courier New, Consolas, Monospace", FONT_SIZE * 2)
        
        self.chapter = 1 # Track game progress
        self.running = True

        self.states = {
            "main_menu": MainMenu(self),
            "overworld_ch1": Overworld_Ch1(self),
            "overworld_ch2": Overworld_Ch2(self),
            "battle": Battle(self),
            "result": Result(self),
        }
        self.stack = []
        self._seed_counter = 1
        self.push_state("main_menu") # Start at the main menu

    def next_seed(self):
        """Provides a deterministic series of seeds for battles."""
        s = self._seed_counter
        self._seed_counter += 1
        return s

    def current(self):
        """Returns the active state from the top of the stack."""
        return self.stack[-1] if self.stack else None

    def push_state(self, name, **kwargs):
        """Pauses the current state and adds a new one on top."""
        st = self.states[name]
        self.stack.append(st)
        st.enter(**kwargs)

    def pop_state(self):
        """Removes the current state and resumes the one below it."""
        if self.stack:
            self.stack.pop().exit()

    def replace_state(self, name, **kwargs):
        """Removes the current state and replaces it with a new one."""
        if self.stack:
            self.stack.pop().exit()
        self.push_state(name, **kwargs)

    def run(self):
        """Main game loop with fixed timestep update."""
        accumulator = 0.0
        prev_ticks = pygame.time.get_ticks()

        while self.running:
            # --- events ---
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                else:
                    cur = self.current()
                    if cur:
                        cur.handle_event(e)

            # --- fixed timestep update ---
            now_ticks = pygame.time.get_ticks()
            frame_dt = (now_ticks - prev_ticks) / 1000.0
            prev_ticks = now_ticks
            accumulator += frame_dt

            # Cap to avoid spiral of death if paused
            accumulator = min(accumulator, 0.25)

            while accumulator >= FIXED_DT:
                cur = self.current()
                if cur:
                    cur.update(FIXED_DT)
                accumulator -= FIXED_DT

            # --- render ---
            cur = self.current()
            if cur:
                cur.draw(self.screen)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit(0)

if __name__ == "__main__":
    Game().run()
