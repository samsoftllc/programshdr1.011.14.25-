#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prgram.py — Single-file Pygame platformer with 32 original levels
------------------------------------------------------------------
This script is an original, fan-made platformer inspired by classic side-scrollers.
It contains no Nintendo assets and no copyrighted level data. Instead, it
procedurally generates 32 distinct levels using math-based patterns.

Controls
- Left / Right arrows: Move
- Z or Space: Jump
- R: Restart current level
- Esc: Quit

Requirements
- Python 3.9+ recommended
- pygame 2.x  (pip install pygame)

Notes
- Everything is embedded in a single file; no external assets required.
- Window size scales a low-res "retro" render to a larger window for clarity.
"""

import sys
import math
import pygame

# --------------------------- Configuration --------------------------- #

TILE       = 16              # base tile size in pixels
BASE_W_T   = 20              # base render width in tiles
BASE_H_T   = 15              # base render height in tiles
BASE_W     = BASE_W_T * TILE # base render width in pixels (logical)
BASE_H     = BASE_H_T * TILE # base render height in pixels (logical)
SCALE      = 3               # screen upscaling factor
SCREEN_W   = BASE_W * SCALE
SCREEN_H   = BASE_H * SCALE
FPS        = 60

GRAVITY    = 0.35            # downward acceleration per frame
MAX_FALL   = 8.0             # clamp fall speed
MOVE_ACC   = 0.5             # horizontal acceleration
MOVE_MAX   = 2.4             # max horizontal speed
FRICTION   = 0.80            # horizontal friction when no input
JUMP_V     = 6.2             # jump velocity (set vertically)

PLAYER_W   = 12              # player collision box size
PLAYER_H   = 14

# Colors (RGB)
COL_BG     = (107, 140, 255)
COL_GROUND = (155, 118, 83)
COL_BLOCK  = (210, 180, 140)
COL_PIPE   = (28, 148, 70)
COL_QBLK   = (230, 200, 72)
COL_COIN   = (255, 220, 0)
COL_FLAG   = (240, 240, 240)
COL_FLAG2  = (200, 32, 32)
COL_PLAYER = (240, 0, 0)
COL_ENEMY  = (125, 62, 0)
COL_TEXT   = (20, 20, 20)
COL_TITLE_BG = (200, 50, 0)  # Red-orange for title sign
COL_GREEN = (34, 139, 34)    # Hill and bush green
COL_BLACK = (0, 0, 0)        # Dots on hill
COL_WHITE = (255, 255, 255)  # Text

# --------------------------- Utility Helpers ------------------------ #

def clamp(value, lo, hi):
    return lo if value < lo else hi if value > hi else value

def sign(x: float) -> int:
    return -1 if x < 0 else (1 if x > 0 else 0)

# --------------------------- Level Generation ----------------------- #

SOLIDS = set(['X', '#', 'P', '?'])  # tiles that are solid
COINS  = set(['o'])                 # tiles that are coins
GOAL   = 'F'                        # goal tile (flag)
SPAWN  = 'S'                        # spawn marker

class Level:
    """
    Procedurally generated level.
    Produces deterministic layouts (no RNG) based on level_index using sin/cos.
    """
    def __init__(self, level_index: int):
        self.index = level_index
        self.h = BASE_H_T
        # widen a bit as levels progress (kept reasonable for performance)
        self.w = 180 + (level_index % 6) * 10
        self.grid = self._generate(level_index)
        self.spawn_px = self._find_spawn()
        self.enemies = self._spawn_enemies()
        # precompute solid rect cache for faster collision in the visible band
        self._solid_rect_cache = {}

    def _generate(self, i: int):
        w, h = self.w, self.h
        g = [[' ' for _ in range(w)] for _ in range(h)]

        ground_y = h - 2

        # 1) Flat ground, then carve holes to form simple platforming
        for x in range(w):
            for y in range(ground_y, h):
                g[y][x] = 'X'

        # 2) Holes patterned by a sin curve and stride
        stride = 34 + (i % 7)
        for base in range(28, w - 25, stride):
            span = 2 + ((base + i * 7) % 3)  # 2..4 wide
            # lift ground locally using a small hill to preview the gap
            for dx in range(-6, 6):
                xx = clamp(base + dx, 0, w - 1)
                bump = int(1.5 * math.sin(dx / 6.0 * math.pi))
                for y in range(ground_y - bump, h):
                    g[y][xx] = 'X'
            # cut the hole itself
            for xx in range(base, min(base + span, w - 1)):
                for y in range(ground_y, h):
                    g[y][xx] = ' '

        # 3) Pipes
        for base in range(22, w - 40, 28 + (i % 3) * 5):
            height = 2 + ((base + i) % 3)  # 2..4
            top = ground_y - height
            for y in range(top, ground_y):
                if 0 <= base < w: g[y][base] = 'P'
                if 0 <= base + 1 < w: g[y][base + 1] = 'P'

        # 4) Platforms of bricks and question blocks
        for base in range(12, w - 16, 18 + (i % 5)):
            plat_y = ground_y - 4 - (((base // 11) + i) % 3) * 2
            length = 4 + ((base + i) % 3)  # 4..6
            for dx in range(length):
                x = base + dx
                if 0 <= x < w and 2 <= plat_y < ground_y - 1:
                    g[plat_y][x] = '#'
            # insert a question block near middle
            qx = base + length // 2
            if 0 <= qx < w and 2 <= plat_y - 1 < ground_y - 1:
                g[plat_y - 1][qx] = '?'

        # 5) Coin arcs
        for base in range(25, w - 10, 32):
            for k in range(7):
                xx = base + k
                yy = ground_y - 4 - int(3 * math.sin(k / 6.0 * math.pi))
                if 0 <= xx < w and 2 <= yy < ground_y - 1:
                    g[yy][xx] = 'o'

        # 6) Start position and Goal flag
        g[ground_y - 1][2] = SPAWN
        g[ground_y - 1][w - 4] = GOAL

        # Ensure the last stretch is safe (no hole right at the end)
        for x in range(w - 8, w - 2):
            for y in range(ground_y, h):
                g[y][x] = 'X'

        return g

    def _find_spawn(self):
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x] == SPAWN:
                    return (x * TILE, y * TILE - (PLAYER_H - (TILE - 2)))
        # fallback
        return (2 * TILE, (self.h - 3) * TILE - (PLAYER_H - (TILE - 2)))

    def _spawn_enemies(self):
        """Create some walking enemies on solid ground segments."""
        enemies = []
        ground_y = self.h - 2
        for x in range(8, self.w - 8, 14 + (self.index % 5)):
            # place only if ground is present and not a hole
            if self.grid[ground_y][x] == 'X' and self.grid[ground_y][x + 1] == 'X':
                ex = (x + 0.2) * TILE
                ey = (ground_y - 1) * TILE + (TILE - PLAYER_H)
                enemies.append(Enemy(ex, ey))
        return enemies

    def in_bounds(self, tx, ty):
        return 0 <= tx < self.w and 0 <= ty < self.h

    def tile(self, tx, ty):
        if not self.in_bounds(tx, ty):
            # out-of-bounds above is empty; sides/below behave like solid to keep camera/physics stable
            return 'X' if ty >= self.h else ' '
        return self.grid[ty][tx]

    def set_tile(self, tx, ty, ch):
        if self.in_bounds(tx, ty):
            self.grid[ty][tx] = ch
            # Invalidate cache for this column region
            self._solid_rect_cache.clear()

    def rects_near(self, rect: pygame.Rect):
        """Return solid tile rects near the given rect to check collisions efficiently."""
        key = (rect.left // TILE, rect.top // TILE, rect.right // TILE, rect.bottom // TILE)
        if key in self._solid_rect_cache:
            return self._solid_rect_cache[key]

        tiles = []
        tx0 = clamp(rect.left // TILE - 1, 0, self.w - 1)
        tx1 = clamp(rect.right // TILE + 1, 0, self.w - 1)
        ty0 = clamp(rect.top // TILE - 1, 0, self.h - 1)
        ty1 = clamp(rect.bottom // TILE + 1, 0, self.h - 1)
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                ch = self.tile(tx, ty)
                if ch in SOLIDS:
                    tiles.append(pygame.Rect(tx * TILE, ty * TILE, TILE, TILE))
        self._solid_rect_cache[key] = tiles
        return tiles

# --------------------------- Entities -------------------------------- #

class Player:
    def __init__(self, px, py):
        # position is top-left float for subpixel movement
        self.x = float(px)
        self.y = float(py)
        self.vx = 0.0
        self.vy = 0.0
        self.rect = pygame.Rect(int(self.x), int(self.y), PLAYER_W, PLAYER_H)
        self.on_ground = False
        self.lives = 3
        self.coins = 0
        self.dead = False
        self.invuln_timer = 0
        self.prev_bottom = self.rect.bottom

    def respawn(self, px, py):
        self.x = float(px)
        self.y = float(py)
        self.vx = 0.0
        self.vy = 0.0
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.on_ground = False
        self.dead = False
        self.invuln_timer = 60

    def update(self, level: Level, keys):
        self.prev_bottom = self.rect.bottom

        # Input
        ax = 0.0
        if keys[pygame.K_LEFT]:
            ax -= MOVE_ACC
        if keys[pygame.K_RIGHT]:
            ax += MOVE_ACC
        # accelerate
        self.vx += ax
        self.vx = clamp(self.vx, -MOVE_MAX, MOVE_MAX)
        # friction when no input
        if ax == 0.0:
            self.vx *= FRICTION
            if abs(self.vx) < 0.01:
                self.vx = 0.0

        # Jump
        if (keys[pygame.K_z] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vy = -JUMP_V
            self.on_ground = False

        # Gravity
        self.vy = clamp(self.vy + GRAVITY, -99, MAX_FALL)

        # Horizontal movement & collisions
        self.x += self.vx
        self.rect.x = int(self.x)
        for tile_rect in level.rects_near(self.rect):
            if self.rect.colliderect(tile_rect):
                if self.vx > 0:
                    self.rect.right = tile_rect.left
                elif self.vx < 0:
                    self.rect.left = tile_rect.right
                self.x = float(self.rect.x)
                self.vx = 0.0

        # Vertical movement & collisions
        self.y += self.vy
        self.rect.y = int(self.y)
        self.on_ground = False
        bumped_head = False
        head_bump_tiles = []

        for tile_rect in level.rects_near(self.rect):
            if self.rect.colliderect(tile_rect):
                tx = tile_rect.x // TILE
                ty = tile_rect.y // TILE
                if self.vy > 0:
                    # moving down; stand on tile
                    self.rect.bottom = tile_rect.top
                    self.y = float(self.rect.y)
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0:
                    # moving up; hit head
                    self.rect.top = tile_rect.bottom
                    self.y = float(self.rect.y)
                    self.vy = 0.0
                    bumped_head = True
                    head_bump_tiles.append((tx, ty))

        # Handle head bumps: question blocks create a coin; bricks stay solid
        if bumped_head:
            for (tx, ty) in head_bump_tiles:
                ch = level.tile(tx, ty)
                if ch == '?':
                    # convert to a used block and spawn a coin one tile above if empty
                    level.set_tile(tx, ty, '#')
                    if level.tile(tx, ty - 1) == ' ':
                        level.set_tile(tx, ty - 1, 'o')

        # Coin collection and goal check
        tx0 = clamp(self.rect.left // TILE, 0, level.w - 1)
        tx1 = clamp(self.rect.right // TILE, 0, level.w - 1)
        ty0 = clamp(self.rect.top // TILE, 0, level.h - 1)
        ty1 = clamp(self.rect.bottom // TILE, 0, level.h - 1)
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                ch = level.tile(tx, ty)
                if ch in COINS:
                    level.set_tile(tx, ty, ' ')
                    self.coins += 1

        # Fell into void?
        if self.rect.top > level.h * TILE + TILE * 2:
            self.dead = True

        # Invulnerability frames after respawn
        if self.invuln_timer > 0:
            self.invuln_timer -= 1

    def draw(self, surf, cam_x):
        # simple rectangle for the player; blink if invulnerable
        if self.invuln_timer % 6 < 3 and self.invuln_timer > 0:
            return
        r = pygame.Rect(self.rect.x - cam_x, self.rect.y, self.rect.w, self.rect.h)
        pygame.draw.rect(surf, COL_PLAYER, r)

class Enemy:
    """Simple walking enemy that turns at edges and walls."""
    def __init__(self, px, py):
        self.x = float(px)
        self.y = float(py)
        self.vx = -1.0
        self.vy = 0.0
        self.rect = pygame.Rect(int(self.x), int(self.y), 14, 14)
        self.alive = True

    def update(self, level: Level):
        if not self.alive:
            return
        # gravity
        self.vy = clamp(self.vy + GRAVITY, -99, MAX_FALL)

        # try to keep walking; detect edge
        ahead_x = self.rect.centerx + (8 * sign(self.vx))
        foot_y  = self.rect.bottom + 1
        tx = clamp(ahead_x // TILE, 0, level.w - 1)
        ty = clamp(foot_y // TILE, 0, level.h - 1)
        under = level.tile(tx, ty)
        if under not in SOLIDS:
            self.vx *= -1

        # Horizontal
        self.x += self.vx
        self.rect.x = int(self.x)
        for tile_rect in level.rects_near(self.rect):
            if self.rect.colliderect(tile_rect):
                if self.vx > 0: self.rect.right = tile_rect.left
                else:           self.rect.left  = tile_rect.right
                self.x = float(self.rect.x)
                self.vx *= -1

        # Vertical
        self.y += self.vy
        self.rect.y = int(self.y)
        for tile_rect in level.rects_near(self.rect):
            if self.rect.colliderect(tile_rect):
                if self.vy > 0:
                    self.rect.bottom = tile_rect.top
                    self.y = float(self.rect.y)
                    self.vy = 0.0
                elif self.vy < 0:
                    self.rect.top = tile_rect.bottom
                    self.y = float(self.rect.y)
                    self.vy = 0.0

    def stomp(self):
        self.alive = False

    def draw(self, surf, cam_x):
        if not self.alive:
            return
        r = pygame.Rect(self.rect.x - cam_x, self.rect.y, self.rect.w, self.rect.h)
        pygame.draw.rect(surf, COL_ENEMY, r)

# --------------------------- Renderer -------------------------------- #

def draw_level_tiles(surf, level: Level, cam_x: int):
    """Draw only the visible slice of tiles."""
    w_vis_tiles = BASE_W // TILE + 2 + 2 # margin
    tx0 = clamp(cam_x // TILE - 1, 0, level.w - 1)
    tx1 = clamp(tx0 + w_vis_tiles, 0, level.w - 1)

    for ty in range(level.h):
        for tx in range(tx0, tx1 + 1):
            ch = level.tile(tx, ty)
            if ch == ' ':
                continue
            x = tx * TILE - cam_x
            y = ty * TILE
            r = pygame.Rect(x, y, TILE, TILE)
            if ch == 'X':
                pygame.draw.rect(surf, COL_GROUND, r)
            elif ch == '#':
                pygame.draw.rect(surf, COL_BLOCK, r)
                pygame.draw.rect(surf, (0,0,0), r, 1)
            elif ch == '?':
                pygame.draw.rect(surf, COL_QBLK, r)
                pygame.draw.rect(surf, (0,0,0), r, 1)
            elif ch == 'P':
                pygame.draw.rect(surf, COL_PIPE, r)
                pygame.draw.rect(surf, (0,0,0), r, 1)
            elif ch == 'o':
                pygame.draw.circle(surf, COL_COIN, (x + TILE // 2, y + TILE // 2), TILE // 3)
            elif ch == 'F':
                # flag pole and flag
                pole = pygame.Rect(x + TILE // 2 - 1, y - 8, 3, TILE + 8)
                pygame.draw.rect(surf, COL_FLAG, pole)
                flag = pygame.Rect(x + TILE // 2 + 2, y + 2, TILE, TILE // 2)
                pygame.draw.rect(surf, COL_FLAG2, flag)

# --------------------------- Game Loop -------------------------------- #

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Ultra Mario 2D Bros — 32 Levels")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.base_surf = pygame.Surface((BASE_W, BASE_H)).convert()
        self.clock = pygame.time.Clock()
        self.big_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 10)

        self.level_no = 1
        self.max_levels = 32
        self.level = Level(self.level_no)
        self.player = Player(*self.level.spawn_px)

        self.state = "menu"  # menu | play | win | gameover

    def reset_level(self):
        self.level = Level(self.level_no)
        self.player.respawn(*self.level.spawn_px)

    def next_level(self):
        self.level_no += 1
        if self.level_no > self.max_levels:
            self.state = "win"
        else:
            self.reset_level()

    def handle_player_enemy_interactions(self):
        # Player vs Enemy interactions (stomp or hurt)
        for e in self.level.enemies:
            if not e.alive:
                continue
            if self.player.rect.colliderect(e.rect):
                # Stomp check: player was above and moving down
                if self.player.prev_bottom <= e.rect.top and self.player.vy > 0:
                    e.stomp()
                    self.player.vy = -JUMP_V * 0.7  # bounce
                    self.player.on_ground = False
                else:
                    if self.player.invuln_timer == 0:
                        self.player.lives -= 1
                        if self.player.lives <= 0:
                            self.state = "gameover"
                        else:
                            self.player.respawn(*self.level.spawn_px)

    def draw_menu(self):
        self.base_surf.fill(COL_BG)

        # Top HUD
        hud_y = 10
        mario_text = self.small_font.render("MARIO", True, COL_WHITE)
        self.base_surf.blit(mario_text, (20, hud_y))
        score_text = self.small_font.render("000000", True, COL_WHITE)
        self.base_surf.blit(score_text, (80, hud_y))
        pygame.draw.circle(self.base_surf, COL_COIN, (150, hud_y + 5), 4)
        coin_count = self.small_font.render("x00", True, COL_WHITE)
        self.base_surf.blit(coin_count, (160, hud_y))
        world_text = self.small_font.render("WORLD", True, COL_WHITE)
        self.base_surf.blit(world_text, (200, hud_y))
        level_text = self.small_font.render("1-1", True, COL_WHITE)
        self.base_surf.blit(level_text, (250, hud_y))
        time_text = self.small_font.render("TIME", True, COL_WHITE)
        self.base_surf.blit(time_text, (280, hud_y))

        # Title sign
        sign_rect = pygame.Rect(60, 40, 200, 40)
        pygame.draw.rect(self.base_surf, COL_TITLE_BG, sign_rect)
        pygame.draw.rect(self.base_surf, COL_BLACK, sign_rect, 1)
        title_upper = self.big_font.render("ULTRA", True, COL_WHITE)
        self.base_surf.blit(title_upper, (sign_rect.centerx - title_upper.get_width() // 2, sign_rect.top + 2))
        title_lower = self.big_font.render("MARIO 2D BROS.", True, COL_WHITE)
        self.base_surf.blit(title_lower, (sign_rect.centerx - title_lower.get_width() // 2, sign_rect.top + 20))

        # Copyright
        copy_text = self.small_font.render("©1985 © Samsoft 2025", True, COL_WHITE)
        self.base_surf.blit(copy_text, (BASE_W // 2 - copy_text.get_width() // 2, 85))

        # Player options
        opt_y = 110
        mushroom_rect = pygame.Rect(100, opt_y, 8, 8)  # Simple mushroom icon
        pygame.draw.ellipse(self.base_surf, (255, 0, 0), mushroom_rect)
        opt1_text = self.small_font.render("1 PLAYER GAME", True, COL_WHITE)
        self.base_surf.blit(opt1_text, (110, opt_y))
        opt2_text = self.small_font.render("2 PLAYER GAME", True, COL_WHITE)  # Placeholder, though not functional
        self.base_surf.blit(opt2_text, (110, opt_y + 15))

        # Landscape
        ground_y = 180
        # Hill
        hill_points = [(80, ground_y), (120, 140), (160, ground_y)]
        pygame.draw.polygon(self.base_surf, COL_GREEN, hill_points)
        # Dots on hill
        pygame.draw.circle(self.base_surf, COL_BLACK, (110, 150), 2)
        pygame.draw.circle(self.base_surf, COL_BLACK, (130, 155), 2)
        pygame.draw.circle(self.base_surf, COL_BLACK, (100, 160), 2)
        # Bush
        bush_x = 200
        pygame.draw.ellipse(self.base_surf, COL_GREEN, (bush_x, ground_y - 20, 40, 20))
        pygame.draw.ellipse(self.base_surf, COL_GREEN, (bush_x + 10, ground_y - 30, 20, 20))
        pygame.draw.ellipse(self.base_surf, COL_GREEN, (bush_x + 20, ground_y - 20, 20, 20))
        # Mario figure (simple)
        mario_x = 110
        mario_y = 140
        pygame.draw.rect(self.base_surf, COL_PLAYER, (mario_x, mario_y, 12, 14))  # Body
        pygame.draw.rect(self.base_surf, COL_PLAYER, (mario_x + 2, mario_y - 4, 8, 4))  # Hat
        # Top score
        top_text = self.small_font.render("TOP- 000000", True, COL_WHITE)
        self.base_surf.blit(top_text, (160, ground_y - 20))
        # Brick ground
        for x in range(0, BASE_W, TILE):
            pygame.draw.rect(self.base_surf, COL_GROUND, (x, ground_y, TILE, TILE))

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit(0)
                    if self.state == "menu":
                        if event.key in (pygame.K_SPACE, pygame.K_z, pygame.K_RETURN):
                            self.state = "play"
                    if event.key == pygame.K_r and self.state == "play":
                        self.reset_level()
                    if event.key == pygame.K_RETURN and self.state in ("win", "gameover"):
                        self.level_no = 1
                        self.state = "menu"
                        self.reset_level()

            keys = pygame.key.get_pressed()

            # Update
            if self.state == "play":
                self.player.update(self.level, keys)
                for e in self.level.enemies:
                    e.update(self.level)

                self.handle_player_enemy_interactions()

                # Check for goal (touching tile 'F')
                tx0 = clamp(self.player.rect.left // TILE, 0, self.level.w - 1)
                tx1 = clamp(self.player.rect.right // TILE, 0, self.level.w - 1)
                ty0 = clamp(self.player.rect.top // TILE, 0, self.level.h - 1)
                ty1 = clamp(self.player.rect.bottom // TILE, 0, self.level.h - 1)
                touched_goal = False
                for ty in range(ty0, ty1 + 1):
                    for tx in range(tx0, tx1 + 1):
                        if self.level.tile(tx, ty) == GOAL:
                            touched_goal = True
                            break
                    if touched_goal:
                        break
                if touched_goal:
                    self.next_level()

                if self.player.dead:
                    self.player.lives -= 1
                    if self.player.lives <= 0:
                        self.state = "gameover"
                    else:
                        self.player.respawn(*self.level.spawn_px)

            # Camera follows player (logical space)
            cam_x = clamp(int(self.player.rect.centerx - BASE_W // 2), 0, self.level.w * TILE - BASE_W) if self.state == "play" else 0

            # Draw to low-res buffer
            self.base_surf.fill(COL_BG)
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "play":
                draw_level_tiles(self.base_surf, self.level, cam_x)
                # draw enemies
                for e in self.level.enemies:
                    e.draw(self.base_surf, cam_x)
                # draw player
                self.player.draw(self.base_surf, cam_x)

                # HUD
                hud = f"LEVEL {self.level_no}/{self.max_levels}   LIVES {self.player.lives}   COINS {self.player.coins}"
                hud_surf = self.small_font.render(hud, True, COL_TEXT)
                self.base_surf.blit(hud_surf, (4, 4))
            elif self.state == "win":
                msg1 = "YOU WIN!"
                msg2 = "Press Enter to play again."
                s1 = self.small_font.render(msg1, True, COL_TEXT)
                s2 = self.small_font.render(msg2, True, COL_TEXT)
                self.base_surf.blit(s1, (BASE_W // 2 - s1.get_width() // 2, BASE_H // 2 - 20))
                self.base_surf.blit(s2, (BASE_W // 2 - s2.get_width() // 2, BASE_H // 2 + 4))
            elif self.state == "gameover":
                msg1 = "GAME OVER"
                msg2 = "Press Enter to restart."
                s1 = self.small_font.render(msg1, True, COL_TEXT)
                s2 = self.small_font.render(msg2, True, COL_TEXT)
                self.base_surf.blit(s1, (BASE_W // 2 - s1.get_width() // 2, BASE_H // 2 - 20))
                self.base_surf.blit(s2, (BASE_W // 2 - s2.get_width() // 2, BASE_H // 2 + 4))

            # Scale up to window
            surface = pygame.transform.scale(self.base_surf, (SCREEN_W, SCREEN_H))
            self.screen.blit(surface, (0, 0))
            pygame.display.flip()

# --------------------------- Entry Point ----------------------------- #

def main():
    try:
        Game().run()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
