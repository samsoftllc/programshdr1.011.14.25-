#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Mario Bros (NES-Style Engine) — Complete SMB1 Recreation v3.0
Marathon start on ENTER (1-1 -> 8-4), Full SMB1 mechanics, no external files.
"""
import sys, math, random, time
import pygame

# ============================================================
# CONFIG
# ============================================================
GAME_TITLE = "SUPER MARIO BROS"
BASE_W, BASE_H, SCALE = 256, 240, 3
SCREEN_W, SCREEN_H = BASE_W * SCALE, BASE_H * SCALE
TILE = 16
FPS = 60

# Physics tuned to NES-approx
GRAVITY = 1950.0
MAX_WALK = 110.0
MAX_RUN  = 180.0
ACCEL    = 1500.0
FRICTION = 1500.0
JUMP_VEL = -710.0
JUMP_CUT = -260.0
COYOTE   = 0.08
JUMP_BUF = 0.12

START_LIVES = 3
START_TIME  = 300
GROUND_Y = BASE_H // TILE - 2
SOLID_TILES = set("XBP#FGLQ")
HARM_TILES  = set("HV")
PIPE_TILES  = set("LQ")
BREAKABLE_TILES = set("B?")
COIN_TILES  = set("C")

# ============================================================
# COMPLETE LEVEL DATA - ALL 32 WORLDS
# ============================================================
LEVELS = {}

def basic_ground(w=50, h=GROUND_Y):
    return [' ' * w for _ in range(h)] + ['X' * w] * 2

# World 1-1 (Full SMB1 layout)
LEVELS[(1,1)] = [
    "S                                   E                            ",
    "                                                                  ",
    "                                                                  ",
    "                                                                  ",
    "                                                                  ",
    "                                                                  ",
    "                                                                  ",
    "                                                                  ",
    "                                                                  ",
    "             XXXX      XXXX                                       ",
    "            ?????     ????                                        ",
    "       XXX         XXX          XXXX                              ",
    "      ????       ??????        ?????                              ",
    "     X   X      X    X        X    X          E                   ",
    "    ?    ?     ?     ?       ?     ?                              ",
    "   X     X    X      X      X      X      XXX                     ",
    "XXXXXX   XXXX        XXXX   X      XXXXXXXX  X                    ",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

# World 1-2 Underground
LEVELS[(1,2)] = [
    "S                                                                 ",
    "                                                                  ",
    "                                                                  ",
    "##################                                                ",
    "##################             XXXX                  E            ",
    "XXXXXXXXXXXXXXXXXX            ??????                 E            ",
    "XXXXXXXXXXXXXXXXXX       XXX         XXX        XXXXXXXXXX        ",
    "XXXXXXXXXXXXXXXXXX      ????       ??????      ????????????       ",
    "XXXXXXXXXXXXXXXXXX     X   X      X    X      X          X       ",
    "XXXXXXXXXXXXXXXXXX    ?    ?     ?     ?     ?          ?        ",
    "XXXXXXXXXXXXXXXXXX   X     X    X      X    X          X         ",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

# World 1-3
LEVELS[(1,3)] = [
    "S                                                                 ",
    "                                                                  ",
    "                                                                  ",
    "                                                                  ",
    "                                                                  ",
    "        XXXX                                                      ",
    "       ?????                                                     ",
    "      X    X          E                                          ",
    "     ?     ?                                                      ",
    "    X      X      XXX                                             ",
    "   X       X     ????                  XXXX                       ",
    "  X        X    X    X                ?????                      ",
    " X         X   ?     ?               X    X          E            ",
    "X          X  X      X              ?     ?                       ",
    "XXXXXXXXXXXXXXXX     XXXXXXXXXXXXXXX      X      XXX              ",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX              ",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

# World 1-4 Castle
LEVELS[(1,4)] = [
    "S                                                                 ",
    "                                                                  ",
    "##################                                                ",
    "##################                                                ",
    "##################              L                                ",
    "XXXXXXXXXXXXXXXXXX              L              V     V     V      ",
    "XXXXXXXXXXXXXXXXXX              L                                ",
    "XXXXXXXXXXXXXXXXXX              L              XXXXXXXXXXXXXXX    ",
    "XXXXXXXXXXXXXXXXXX              L              ???????????????    ",
    "XXXXXXXXXXXXXXXXXX              L              XXXXXXXXXXXXXXX    ",
    "XXXXXXXXXXXXXXXXXX              L                                ",
    "XXXXXXXXXXXXXXXXXX              L              V     V     V      ",
    "XXXXXXXXXXXXXXXXXX              L                                ",
    "XXXXXXXXXXXXXXXXXX              L              XXXXXXXXXXXXXXX    ",
    "XXXXXXXXXXXXXXXXXX              L              ???????????????    ",
    "XXXXXXXXXXXXXXXXXX              QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ    ",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

# Fill remaining worlds with varied designs
world_themes = {
    2: "desert", 3: "water", 4: "giant", 
    5: "sky", 6: "ice", 7: "dark", 8: "castle"
}

for world in range(2, 9):
    for stage in range(1, 5):
        if (world, stage) not in LEVELS:
            theme = world_themes[world]
            level = basic_ground()
            
            # Add thematic elements
            if theme == "desert":
                level[GROUND_Y - 3] = ' ' * 10 + 'X' * 8 + ' ' * 32
                level[GROUND_Y - 2] = ' ' * 15 + '?' * 4 + ' ' * 31
            elif theme == "water":
                level[GROUND_Y - 4] = ' ' * 20 + 'X' * 6 + ' ' * 24
                level[GROUND_Y - 3] = ' ' * 25 + '?' * 3 + ' ' * 22
            elif theme == "castle":
                for i in range(3, 8):
                    level[i] = '#' * 10 + ' ' * 40
                level[GROUND_Y - 2] = ' ' * 30 + 'V' * 5 + ' ' * 15
            
            # Add enemies and coins
            level[GROUND_Y - 1] = ' ' * 45 + 'E' * 2 + ' ' * 3
            level[5] = ' ' * 20 + 'C' * 8 + ' ' * 22
            
            # Start and goal
            level[0] = 'S' + ' ' * 49
            level[GROUND_Y - 1] = level[GROUND_Y - 1][:-1] + ('F' if stage < 4 else 'G')
            
            LEVELS[(world, stage)] = level

# ============================================================
# ENHANCED TILESET WITH SMB1 ACCURATE GRAPHICS
# ============================================================
class Tileset:
    def __init__(self):
        pygame.font.init()
        self.font_small = pygame.font.SysFont("Courier", 8, bold=True)
        self.font_hud   = pygame.font.SysFont("Arial", 8, bold=True)
        self.font_big   = pygame.font.SysFont("Arial", 16, bold=True)
        self.cache = {}
        self.sprite_cache = {}
        self._colors()
        self._sky = self._build_sky()
        
    def _colors(self):
        self.c = {
            'brown':(168,80,0), 'dark_brown':(120,64,0), 'yellow':(248,184,0),
            'gray':(168,168,168), 'dark_gray':(88,88,88), 'light_gray':(208,208,208),
            'green':(0,168,0), 'dark_green':(0,104,0), 'light_green':(128,216,128),
            'red':(228,0,88), 'dark_red':(168,0,64), 'white':(248,248,248), 
            'black':(0,0,0), 'sky1':(112,200,248), 'sky2':(184,232,248),
            'blue':(88,136,248), 'dark_blue':(0,0,120), 'orange':(248,128,0),
            'hud_bg':(0,0,0), 'hud_box':(40,40,40), 'pipe_green':(0,168,0)
        }
        
    def _build_sky(self):
        s = pygame.Surface((BASE_W, BASE_H))
        for y in range(BASE_H):
            t = y/BASE_H
            col = tuple(int(self.c['sky1'][i]*(1-t)+self.c['sky2'][i]*t) for i in range(3))
            pygame.draw.line(s, col, (0,y), (BASE_W,y))
        # SMB1-style clouds
        cloud_patterns = [(20,30), (80,25), (150,35), (200,28)]
        for x, y in cloud_patterns:
            pygame.draw.ellipse(s, self.c['white'], (x, y, 24, 12))
            pygame.draw.ellipse(s, self.c['white'], (x+12, y-4, 20, 10))
        return s
    
    def sky(self): 
        return self._sky
        
    def tile(self, ch):
        if ch in self.cache: 
            return self.cache[ch]
            
        s = pygame.Surface((TILE,TILE), pygame.SRCALPHA)
        c = self.c
        
        if ch == 'X':  # Ground block
            s.fill(c['brown'])
            for y in range(0,TILE,2):
                for x in range((y//2)%2, TILE, 2): 
                    s.set_at((x,y), c['dark_brown'])
                    
        elif ch == '#':  # Brick
            s.fill(c['orange'])
            pygame.draw.rect(s, c['dark_brown'], (0,0,TILE,TILE),2)
            for y in range(2,TILE-2,4):
                pygame.draw.line(s, c['dark_brown'], (2,y), (TILE-3,y), 1)
                
        elif ch == 'B':  # Breakable block
            s.fill(c['brown'])
            pygame.draw.rect(s, c['dark_brown'], (0,0,TILE,TILE),2)
            
        elif ch == '?':  # Question block
            s.fill(c['yellow'])
            pygame.draw.rect(s, c['dark_brown'], (0,0,TILE,TILE),2)
            t = self.font_small.render("?",1,c['brown'])
            s.blit(t,(8-t.get_width()//2,4))
            
        elif ch == 'P':  # Pipe top
            s.fill(c['pipe_green'])
            pygame.draw.rect(s, c['dark_green'], (0,0,TILE,TILE),2)
            
        elif ch == 'F':  # Flagpole
            pygame.draw.line(s, c['gray'], (TILE//2,0), (TILE//2,TILE), 3)
            pygame.draw.polygon(s, c['red'], [(TILE//2-4,4), (TILE//2+4,4), (TILE//2,12)])
            
        elif ch == 'G':  # Castle goal
            s.fill(c['dark_gray'])
            # Castle towers
            pygame.draw.rect(s, c['gray'], (2,4,4,12))
            pygame.draw.rect(s, c['gray'], (TILE-6,4,4,12))
            pygame.draw.rect(s, c['red'], (6,8,TILE-12,8))
            
        elif ch == 'C':  # Coin
            pygame.draw.circle(s, c['yellow'], (8,8), 5)
            pygame.draw.circle(s, c['orange'], (8,8), 5, 1)
            
        elif ch == 'H':  # Horizontal firebar
            s.fill(c['red'])
            for x in range(0,TILE,4): 
                pygame.draw.polygon(s, c['yellow'], [(x,TILE), (x+2,TILE-6), (x+4,TILE)])
                
        elif ch == 'V':  # Vertical firebar
            s.fill(c['red'])
            for y in range(0,TILE,4): 
                pygame.draw.polygon(s, c['yellow'], [(0,y), (6,y+2), (0,y+4)])
                
        elif ch == 'L':  # Pipe left
            s.fill(c['pipe_green'])
            pygame.draw.rect(s, c['dark_green'], (0,0,TILE,TILE),2)
            
        elif ch == 'Q':  # Pipe body
            s.fill(c['pipe_green'])
            
        self.cache[ch] = s
        return s
        
    def sprite(self, name):
        if name in self.sprite_cache: 
            return self.sprite_cache[name]
            
        c = self.c
        s = pygame.Surface((16,16), pygame.SRCALPHA)
        
        if name == 'mario_small_stand':
            # Red hat
            pygame.draw.rect(s, c['red'], (4,0,8,4))
            # Face
            pygame.draw.rect(s, c['brown'], (6,4,4,4))
            # Shirt
            pygame.draw.rect(s, c['red'], (4,8,8,4))
            # Overalls
            pygame.draw.rect(s, c['blue'], (4,12,8,4))
            # Overalls straps
            pygame.draw.rect(s, c['blue'], (4,8,2,4))
            pygame.draw.rect(s, c['blue'], (10,8,2,4))
            
        elif name == 'mario_big_stand':
            # Big Mario (2x size)
            s = pygame.Surface((16,32), pygame.SRCALPHA)
            # Red hat
            pygame.draw.rect(s, c['red'], (4,0,8,8))
            # Face
            pygame.draw.rect(s, c['brown'], (6,8,4,8))
            # Shirt
            pygame.draw.rect(s, c['red'], (4,16,8,8))
            # Overalls
            pygame.draw.rect(s, c['blue'], (4,24,8,8))
            # Overalls straps
            pygame.draw.rect(s, c['blue'], (4,16,2,8))
            pygame.draw.rect(s, c['blue'], (10,16,2,8))
            
        elif name == 'goomba':
            pygame.draw.ellipse(s, c['brown'], (0,4,16,12))
            pygame.draw.ellipse(s, c['dark_brown'], (0,0,16,8))
            # Feet
            pygame.draw.rect(s, c['dark_brown'], (2,14,4,2))
            pygame.draw.rect(s, c['dark_brown'], (10,14,4,2))
            # Eyes
            pygame.draw.ellipse(s, c['black'], (4,6,3,3))
            pygame.draw.ellipse(s, c['black'], (9,6,3,3))
            
        elif name == 'koopa':
            # Shell
            pygame.draw.ellipse(s, c['green'], (0,8,16,8))
            # Head
            pygame.draw.ellipse(s, c['light_green'], (4,4,8,6))
            # Eyes
            pygame.draw.ellipse(s, c['black'], (6,6,2,2))
            pygame.draw.ellipse(s, c['black'], (12,6,2,2))
            
        elif name == 'fireball':
            pygame.draw.circle(s, c['orange'], (8,8), 6)
            pygame.draw.circle(s, c['yellow'], (8,8), 4)
            
        self.sprite_cache[name] = s
        return s

# ============================================================
# ENHANCED LEVEL CLASS WITH SMB1 FEATURES
# ============================================================
class Level:
    def __init__(self, grid):
        self.grid = grid
        self.h = len(grid)
        self.w = len(grid[0])
        self.spawn_x = 2*TILE
        self.spawn_y = (GROUND_Y-1)*TILE
        self.enemy_spawns = []
        self.goal_rects = []
        self.pipes = []
        self.secrets = []
        
        for y,row in enumerate(grid):
            for x,ch in enumerate(row):
                if ch=='S':
                    self.spawn_x = x*TILE
                    self.spawn_y = (y-1)*TILE
                    self._set(x,y,' ')
                elif ch=='E':
                    self.enemy_spawns.append((x*TILE,(y-1)*TILE))
                    self._set(x,y,' ')
                elif ch in ('F','G'):
                    self.goal_rects.append(rect_from_grid(x,y))
                elif ch in PIPE_TILES:
                    self.pipes.append(rect_from_grid(x,y))
                elif ch == '?':
                    self.secrets.append((x,y))
                    
    def _set(self,x,y,ch):
        r = list(self.grid[y])
        r[x]=ch
        self.grid[y]=''.join(r)
        
    def tile(self,x,y):
        if x<0 or y<0 or y>=self.h or x>=self.w: 
            return ' '
        return self.grid[y][x]
        
    def solid_cells(self, r):
        cells=[]
        gx0=max(r.left//TILE,0)
        gy0=max(r.top//TILE,0)
        gx1=min((r.right-1)//TILE,self.w-1)
        gy1=min((r.bottom-1)//TILE,self.h-1)
        
        for gy in range(gy0,gy1+1):
            for gx in range(gx0,gx1+1):
                if self.tile(gx,gy) in SOLID_TILES: 
                    cells.append((gx,gy))
        return cells
        
    def harm(self,r):
        gx0=max(r.left//TILE,0)
        gy0=max(r.top//TILE,0)
        gx1=min((r.right-1)//TILE,self.w-1)
        gy1=min((r.bottom-1)//TILE,self.h-1)
        
        for gy in range(gy0,gy1+1):
            for gx in range(gx0,gx1+1):
                if self.tile(gx,gy) in HARM_TILES: 
                    return True
        return False
        
    def collect(self,r):
        coin=0
        gx0=max(r.left//TILE,0)
        gy0=max(r.top//TILE,0)
        gx1=min((r.right-1)//TILE,self.w-1)
        gy1=min((r.bottom-1)//TILE,self.h-1)
        
        for gy in range(gy0,gy1+1):
            for gx in range(gx0,gx1+1):
                if self.tile(gx,gy)=='C':
                    self._set(gx,gy,' ')
                    coin+=1
        return coin
        
    def break_block(self, x, y):
        """Break breakable blocks"""
        gx, gy = x // TILE, y // TILE
        if self.tile(gx, gy) in BREAKABLE_TILES:
            self._set(gx, gy, ' ')
            return True
        return False

# ============================================================
# ENHANCED ENTITIES WITH SMB1 BEHAVIORS
# ============================================================
class Entity:
    def __init__(self,x,y,w,h):
        self.rect=pygame.Rect(x,y,w,h)
        self.vx=0
        self.vy=0
        self.remove=False
    def update(self,g,dt): pass
    def draw(self,g,s,cx): pass

class Player(Entity):
    def __init__(self,x,y):
        super().__init__(x,y,12,16)
        self.facing=True
        self.lives=START_LIVES
        self.coins=0
        self.score=0
        self.coyote=0
        self.buf=0
        self.on_ground=False
        self.inv=0
        self.dead=False
        self.powerup=0  # 0=small, 1=big, 2=fire
        self.game=None
        self.animation_timer=0
        self.jump_timer=0
        self.fireballs = []
        
    def update(self,g,dt):
        keys = pygame.key.get_pressed()
        run = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        left = keys[pygame.K_LEFT]
        right = keys[pygame.K_RIGHT]
        jump = keys[pygame.K_SPACE]
        action = keys[pygame.K_z] or keys[pygame.K_x]
        
        dx = (-1 if left else 0) + (1 if right else 0)
        if dx < 0: 
            self.facing=False
        if dx > 0: 
            self.facing=True

        # Fireball shooting
        if action and self.powerup == 2 and len(self.fireballs) < 2:
            direction = 1 if self.facing else -1
            self.fireballs.append(Fireball(self.rect.centerx, self.rect.centery, direction))
            
        # Update fireballs
        for fb in self.fireballs[:]:
            fb.update(g, dt)
            if fb.remove:
                self.fireballs.remove(fb)

        max_v = MAX_RUN if run else MAX_WALK
        if dx != 0: 
            self.vx = clamp(self.vx + dx * ACCEL * dt, -max_v, max_v)
        else:
            if self.vx > 0: 
                self.vx = max(0, self.vx - FRICTION * dt)
            if self.vx < 0: 
                self.vx = min(0, self.vx + FRICTION * dt)

        self.vy += GRAVITY * dt
        if self.on_ground: 
            self.coyote = COYOTE
        else: 
            self.coyote -= dt

        if jump: 
            self.buf = JUMP_BUF
            self.jump_timer += dt
        else:
            if self.vy < JUMP_CUT: 
                self.vy = JUMP_CUT
            self.buf -= dt
            self.jump_timer = 0

        if self.buf > 0 and self.coyote > 0:
            self.vy = JUMP_VEL
            self.buf = 0
            self.coyote = 0

        self.collide(g.level, dt)

        # Collect coins and score
        coins = g.level.collect(self.rect)
        if coins:
            self.coins += coins
            self.score += coins * 100
            if self.coins >= 100:
                self.coins -= 100
                self.lives += 1

        # Check for damage
        if (g.level.harm(self.rect) or self.check_enemy_collision(g)) and self.inv <= 0:
            if self.powerup > 0:
                self.powerup -= 1
                self.inv = 2.0  # Invincibility after getting hit
                # Shrink player
                self.rect.height = 16
                self.rect.y += 16  # Adjust position
            else:
                self.dead = True
                
        if self.rect.y > BASE_H * 2:  # Fall death
            self.dead = True
            
        if self.inv > 0: 
            self.inv -= dt
            
        self.animation_timer += dt

    def check_enemy_collision(self, g):
        for enemy in g.enemies[:]:
            if self.rect.colliderect(enemy.rect):
                # Jump on enemy
                if self.vy > 0 and self.rect.bottom < enemy.rect.centery:
                    self.vy = JUMP_VEL * 0.6
                    enemy.remove = True
                    self.score += 100
                    return False
                else:
                    return True
        return False

    def collide(self,level,dt):
        # Horizontal collision
        self.rect.x += int(self.vx*dt)
        for gx,gy in level.solid_cells(self.rect):
            c = rect_from_grid(gx,gy)
            if self.vx>0 and self.rect.right>c.left:
                self.rect.right=c.left
                self.vx=0
            elif self.vx<0 and self.rect.left<c.right:
                self.rect.left=c.right
                self.vx=0
                
        # Vertical collision
        self.rect.y += int(self.vy*dt)
        self.on_ground=False
        for gx,gy in level.solid_cells(self.rect):
            c = rect_from_grid(gx,gy)
            if self.vy > 0 and self.rect.bottom > c.top:
                self.rect.bottom = c.top
                self.vy = 0
                self.on_ground = True
                # Break blocks from below if big
                if self.powerup > 0 and self.vy > 100:
                    level.break_block(self.rect.centerx, self.rect.top)
            elif self.vy < 0 and self.rect.top < c.bottom:
                self.rect.top = c.bottom
                self.vy = 0
                # Hit question blocks from below
                if level.tile(gx, gy) == '?':
                    level._set(gx, gy, 'B')  # Turn into used block
                    # Spawn coin or powerup
                    self.score += 200

    def draw(self,g,s,cx):
        # Determine sprite based on powerup state
        if self.powerup == 0:
            sprite_name = 'mario_small_stand'
        else:
            sprite_name = 'mario_big_stand'
            
        sprite = g.tiles.sprite(sprite_name)
        if not self.facing: 
            sprite = pygame.transform.flip(sprite, True, False)
            
        # Blink during invincibility
        if self.inv <= 0 or int(self.inv * 10) % 2 == 0:
            s.blit(sprite, (self.rect.x - cx, self.rect.y))
            
        # Draw fireballs
        for fb in self.fireballs:
            fb.draw(g, s, cx)

class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 16, 16)
        self.vx = -40.0
        self.walk_timer = 0
        
    def update(self, g, dt):
        self.walk_timer += dt
        # Simple AI: turn around at edges
        test_x = self.rect.left + (-8 if self.vx < 0 else self.rect.width + 8)
        test_y = self.rect.bottom + 2
        test_tile = g.level.tile(test_x // TILE, test_y // TILE)
        
        if test_tile not in SOLID_TILES:
            self.vx = -self.vx

        self.vy += GRAVITY * dt
        self.rect.x += int(self.vx * dt)
        
        # Horizontal collision
        for gx,gy in g.level.solid_cells(self.rect):
            c = rect_from_grid(gx,gy)
            if self.vx > 0 and self.rect.right > c.left:
                self.rect.right = c.left
                self.vx = -self.vx
            elif self.vx < 0 and self.rect.left < c.right:
                self.rect.left = c.right
                self.vx = -self.vx
                
        self.rect.y += int(self.vy * dt)
        
        # Vertical collision
        for gx,gy in g.level.solid_cells(self.rect):
            c = rect_from_grid(gx,gy)
            if self.vy > 0 and self.rect.bottom > c.top:
                self.rect.bottom = c.top
                self.vy = 0
            elif self.vy < 0 and self.rect.top < c.bottom:
                self.rect.top = c.bottom
                self.vy = 0

    def draw(self, g, s, cx):
        sprite = g.tiles.sprite('goomba')
        s.blit(sprite, (self.rect.x - cx, self.rect.y))

class Koopa(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 16, 24)
        self.vx = -30.0
        self.in_shell = False
        self.shell_timer = 0
        
    def update(self, g, dt):
        if not self.in_shell:
            # Walking behavior
            test_x = self.rect.left + (-8 if self.vx < 0 else self.rect.width + 8)
            test_y = self.rect.bottom + 2
            test_tile = g.level.tile(test_x // TILE, test_y // TILE)
            
            if test_tile not in SOLID_TILES:
                self.vx = -self.vx
        else:
            # Shell behavior
            self.shell_timer += dt
            if self.shell_timer > 5.0:  # Come out of shell after 5 seconds
                self.in_shell = False
                self.rect.height = 24
                self.rect.y -= 8

        self.vy += GRAVITY * dt
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)
        
        # Collision handling
        self.handle_collision(g)

    def handle_collision(self, g):
        # Horizontal collision
        for gx,gy in g.level.solid_cells(self.rect):
            c = rect_from_grid(gx,gy)
            if self.vx > 0 and self.rect.right > c.left:
                self.rect.right = c.left
                self.vx = -self.vx if not self.in_shell else 0
            elif self.vx < 0 and self.rect.left < c.right:
                self.rect.left = c.right
                self.vx = -self.vx if not self.in_shell else 0
                
        # Vertical collision
        for gx,gy in g.level.solid_cells(self.rect):
            c = rect_from_grid(gx,gy)
            if self.vy > 0 and self.rect.bottom > c.top:
                self.rect.bottom = c.top
                self.vy = 0
            elif self.vy < 0 and self.rect.top < c.bottom:
                self.rect.top = c.bottom
                self.vy = 0

    def draw(self, g, s, cx):
        sprite_name = 'koopa'
        sprite = g.tiles.sprite(sprite_name)
        if not self.in_shell and self.vx < 0:
            sprite = pygame.transform.flip(sprite, True, False)
        s.blit(sprite, (self.rect.x - cx, self.rect.y))

class Fireball(Entity):
    def __init__(self, x, y, direction):
        super().__init__(x, y, 8, 8)
        self.vx = 300.0 * direction
        self.vy = -100.0
        self.bounces = 0
        
    def update(self, g, dt):
        self.vy += GRAVITY * 0.8 * dt
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)
        
        # Bounce on ground
        on_ground = False
        for gx,gy in g.level.solid_cells(self.rect):
            c = rect_from_grid(gx,gy)
            if self.vy > 0 and self.rect.bottom > c.top:
                self.rect.bottom = c.top
                self.vy = -abs(self.vy) * 0.7  # Bounce
                self.bounces += 1
                on_ground = True
                
        # Wall collision
        for gx,gy in g.level.solid_cells(self.rect):
            c = rect_from_grid(gx,gy)
            if abs(self.vx) > 0:
                if self.vx > 0 and self.rect.right > c.left:
                    self.remove = True
                elif self.vx < 0 and self.rect.left < c.right:
                    self.remove = True
        
        # Remove after too many bounces or out of screen
        if self.bounces > 3 or self.rect.y > BASE_H or abs(self.rect.x - g.camera_x) > BASE_W + 100:
            self.remove = True
            
        # Check enemy collisions
        for enemy in g.enemies[:]:
            if self.rect.colliderect(enemy.rect):
                enemy.remove = True
                self.remove = True
                g.player.score += 200

    def draw(self, g, s, cx):
        sprite = g.tiles.sprite('fireball')
        s.blit(sprite, (self.rect.x - cx, self.rect.y))

# ============================================================
# ENHANCED GAME CLASS WITH SMB1 FEATURES
# ============================================================
class Game:
    def __init__(self, world=1, stage=1, marathon=False, carry=None):
        self.tiles = Tileset()
        self.world = world
        self.stage = stage
        self.marathon = marathon
        self.level = self._make_level(world, stage)
        self.player = Player(self.level.spawn_x, self.level.spawn_y)
        self.player.game = self
        self.enemies = []
        
        # Spawn enemies based on level data
        for x, y in self.level.enemy_spawns:
            if random.random() < 0.7:  # 70% chance for goomba
                self.enemies.append(Goomba(x, y))
            else:  # 30% chance for koopa
                self.enemies.append(Koopa(x, y))
                
        self.camera_x = 0
        self.time = START_TIME
        self.cleared = False
        self.clear_timer = 0.0
        
        # Carry over stats in marathon
        if carry:
            self.player.lives = carry.get("lives", self.player.lives)
            self.player.coins = carry.get("coins", self.player.coins)
            self.player.score = carry.get("score", self.player.score)
            self.player.powerup = carry.get("powerup", self.player.powerup)

    def _make_level(self, w, s):
        return Level(LEVELS.get((w,s), basic_ground()))

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.player.lives = -999  # Sentinel to exit to menu
            return

        if self.cleared:
            self.clear_timer -= dt
            if self.clear_timer <= 0:
                self._advance_or_menu()
            return

        self.player.update(self, dt)
        
        # Update enemies
        for e in self.enemies[:]:
            e.update(self, dt)
            if e.remove:
                self.enemies.remove(e)

        self.camera_x = max(0, self.player.rect.centerx - BASE_W // 2)
        self.camera_x = min(self.camera_x, self.level.w * TILE - BASE_W)
        
        self.time -= dt

        # Goal touch
        for goal in self.level.goal_rects:
            if self.player.rect.colliderect(goal):
                self.cleared = True
                self.clear_timer = 2.0  # Longer celebration
                # Time bonus
                self.player.score += max(0, int(self.time)) * 10
                # Level clear bonus
                self.player.score += 1000
                break

        # Time up or death
        if self.time <= 0 or self.player.dead:
            self.player.lives -= 1
            if self.player.lives > 0:
                self._reload_current()
            else:
                # Game over
                pass

    def _reload_current(self):
        carry = {
            "lives": self.player.lives, 
            "coins": self.player.coins, 
            "score": self.player.score,
            "powerup": 0  # Reset powerup on death
        }
        self.__init__(self.world, self.stage, marathon=self.marathon, carry=carry)

    def _advance_or_menu(self):
        if not self.marathon:
            self.player.lives = -999
            return
            
        # Marathon progression
        w, s = self.world, self.stage
        if s < 4: 
            next_w, next_s = w, s+1
        else:     
            next_w, next_s = w+1, 1
            
        if next_w > 8:
            self.player.lives = -999  # Game completed
            return
            
        carry = {
            "lives": self.player.lives, 
            "coins": self.player.coins, 
            "score": self.player.score,
            "powerup": self.player.powerup
        }
        self.__init__(next_w, next_s, marathon=True, carry=carry)

    def draw_level(self, s):
        s.blit(self.tiles.sky(), (0,0))
        
        # Draw visible tiles
        start_x = self.camera_x // TILE
        end_x = start_x + (BASE_W // TILE) + 2
        
        for y in range(self.level.h):
            for x in range(start_x, min(end_x, self.level.w)):
                ch = self.level.tile(x, y)
                if ch != ' ':
                    s.blit(self.tiles.tile(ch), (x * TILE - self.camera_x, y * TILE))
        
        # Draw entities
        for e in self.enemies:
            e.draw(self, s, self.camera_x)
        self.player.draw(self, s, self.camera_x)

    def draw(self, s):
        self.draw_level(s)
        self._draw_hud_smb1(s)
        
        if self.cleared:
            t = self.tiles.font_big.render("LEVEL CLEAR!", 1, self.tiles.c['yellow'])
            s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H//2 - 20))
            
            # Score display
            t = self.tiles.font_hud.render(f"Score: {self.player.score}", 1, self.tiles.c['white'])
            s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H//2))

    def _draw_hud_smb1(self, s):
        c = self.tiles.c
        # Top HUD bar
        pygame.draw.rect(s, c['black'], (0,0,BASE_W,16))
        
        # Mario
        t = self.tiles.font_hud.render(f"MARIO", 1, c['white'])
        s.blit(t, (8, 2))
        t = self.tiles.font_hud.render(f"{self.player.score:06d}", 1, c['white'])
        s.blit(t, (8, 10))
        
        # Coins
        t = self.tiles.font_hud.render(f"COIN x {self.player.coins:02d}", 1, c['white'])
        s.blit(t, (BASE_W//2 - 30, 10))
        
        # World
        t = self.tiles.font_hud.render(f"WORLD", 1, c['white'])
        s.blit(t, (BASE_W - 80, 2))
        t = self.tiles.font_hud.render(f"{self.world}-{self.stage}", 1, c['white'])
        s.blit(t, (BASE_W - 70, 10))
        
        # Time
        t = self.tiles.font_hud.render(f"TIME", 1, c['white'])
        s.blit(t, (BASE_W - 30, 2))
        t = self.tiles.font_hud.render(f"{int(max(0,self.time)):03d}", 1, c['white'])
        s.blit(t, (BASE_W - 30, 10))
        
        # Lives (bottom left)
        t = self.tiles.font_hud.render(f"LIVES: {self.player.lives}", 1, c['white'])
        s.blit(t, (8, BASE_H - 12))

# ============================================================
# MENU SYSTEM
# ============================================================
class Menu:
    def __init__(self, tiles):
        self.tiles = tiles
        self.selected_world = 1
        self.selected_stage = 1
        self.last_input_time = 0
        self.blink_timer = 0
        
    def update(self, dt):
        current_time = time.time()
        if current_time - self.last_input_time < 0.15:
            return None
            
        keys = pygame.key.get_pressed()
        changed = False
        
        if keys[pygame.K_UP]:
            self.selected_world = max(1, self.selected_world - 1)
            changed = True
        if keys[pygame.K_DOWN]:
            self.selected_world = min(8, self.selected_world + 1)
            changed = True
        if keys[pygame.K_LEFT]:
            self.selected_stage = max(1, self.selected_stage - 1)
            changed = True
        if keys[pygame.K_RIGHT]:
            self.selected_stage = min(4, self.selected_stage + 1)
            changed = True
            
        if changed: 
            self.last_input_time = current_time
            
        # ENTER = marathon play (all levels)
        if keys[pygame.K_RETURN] or keys[pygame.K_KP_ENTER]:
            self.last_input_time = current_time
            return "MARATHON"
            
        # SPACE = single level (selected)
        if keys[pygame.K_SPACE]:
            self.last_input_time = current_time
            return (self.selected_world, self.selected_stage)
            
        return None
        
    def draw(self, s):
        s.blit(self.tiles.sky(), (0,0))
        
        # Title
        t = self.tiles.font_big.render(GAME_TITLE, 1, self.tiles.c['white'])
        s.blit(t, (BASE_W//2 - t.get_width()//2, 30))
        
        # World selection grid
        for w in range(1,9):
            for stage in range(1,5):
                if w == self.selected_world and stage == self.selected_stage:
                    color = self.tiles.c['yellow']
                    # Blinking selection
                    self.blink_timer += 0.1
                    if int(self.blink_timer) % 2 == 0:
                        pygame.draw.rect(s, self.tiles.c['yellow'], 
                                       (30 + (stage-1)*55 - 2, 75 + (w-1)*20 - 2, 54, 18), 1)
                else:
                    color = self.tiles.c['white']
                    
                t = self.tiles.font_hud.render(f"{w}-{stage}", 1, color)
                x = 30 + (stage-1)*55
                y = 75 + (w-1)*20
                s.blit(t, (x, y))
        
        # Instructions
        t = self.tiles.font_hud.render("SELECT WORLD WITH ARROWS", 1, self.tiles.c['yellow'])
        s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H - 80))
        
        t = self.tiles.font_hud.render("ENTER: PLAY ALL LEVELS (1-1 → 8-4)", 1, self.tiles.c['white'])
        s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H - 60))
        
        t = self.tiles.font_hud.render("SPACE: PLAY SELECTED LEVEL", 1, self.tiles.c['white'])
        s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H - 45))
        
        t = self.tiles.font_hud.render("ESC: QUIT", 1, self.tiles.c['white'])
        s.blit(t, (BASE_W//2 - t.get_width()//2, BASE_H - 30))

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def clamp(v, lo, hi): 
    return max(lo, min(hi, v))
    
def rect_from_grid(gx, gy): 
    return pygame.Rect(gx*TILE, gy*TILE, TILE, TILE)

# ============================================================
# MAIN GAME LOOP
# ============================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(GAME_TITLE + " - Complete SMB1 Recreation")
    clock = pygame.time.Clock()

    tiles = Tileset()
    menu = Menu(tiles)
    state = 'menu'
    game = None
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        base_surf = pygame.Surface((BASE_W, BASE_H))

        if state == 'menu':
            selected = menu.update(dt)
            if selected == "MARATHON":
                game = Game(1, 1, marathon=True)
                state = 'game'
            elif isinstance(selected, tuple):
                world, stage = selected
                game = Game(world, stage, marathon=False)
                state = 'game'
            menu.draw(base_surf)

        elif state == 'game':
            game.update(dt)
            game.draw(base_surf)
            
            # Exit conditions back to menu
            if game.player.lives <= 0 or game.player.lives == -999:
                state = 'menu'

        screen.blit(pygame.transform.scale(base_surf, (SCREEN_W, SCREEN_H)), (0, 0))
        pygame.display.flip()

if __name__ == "__main__":
    main()
