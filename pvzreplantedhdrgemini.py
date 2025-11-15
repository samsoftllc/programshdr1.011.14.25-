import pygame
import random

# --- Initialize Pygame ---
pygame.init()
pygame.font.init()

# --- Game Settings ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
GRID_ROWS = 5
GRID_COLS = 9
# Ensure UI_WIDTH is an integer for clean calculations
UI_WIDTH = int(SCREEN_WIDTH * 0.25) 
GAME_AREA_WIDTH = SCREEN_WIDTH - UI_WIDTH
# Calculate cell sizes based on the remaining game area
CELL_WIDTH = GAME_AREA_WIDTH // GRID_COLS
CELL_HEIGHT = SCREEN_HEIGHT // GRID_ROWS


FPS = 30

# --- Colors ---
COLOR_BACKGROUND = (106, 153, 78)  # #6A994E
COLOR_GRID = (116, 163, 88)
COLOR_UI = (188, 71, 73)  # #BC4749
COLOR_TEXT = (242, 232, 207)  # #F2E8CF
COLOR_HIGHLIGHT = (255, 255, 0, 100)
COLOR_SUN = (255, 190, 0)
COLOR_SUNFLOWER = (255, 220, 0)
COLOR_SHOOTER = (60, 179, 113)
COLOR_PROJECTILE = (0, 255, 0)
COLOR_MONSTER = (139, 0, 0)

# --- Asset Definitions (Simple Shapes) ---
PLANT_TYPES = {
    'sunflower': {
        'name': 'Sunflower',
        'cost': 50,
        'health': 50,
        'color': COLOR_SUNFLOWER,
    },
    'shooter': {
        'name': 'Shooter',
        'cost': 100,
        'health': 100,
        'color': COLOR_SHOOTER,
    }
}

MONSTER_TYPES = {
    'walker': {
        'health': 100,
        'speed': 0.5,
        'damage': 10,
        'color': COLOR_MONSTER,
    }
}

# --- Game Font ---
try:
    # Use a common pixel font if available, else default
    FONT = pygame.font.SysFont('Press Start 2P', 20)
except:
    FONT = pygame.font.SysFont(None, 24)
    
FONT_SMALL = pygame.font.SysFont(None, 20)

# --- Entity Classes ---

class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, row, col):
        super().__init__()
        self.plant_type = plant_type
        self.row = row
        self.col = col
        self.health = PLANT_TYPES[plant_type]['health']
        
        self.rect = pygame.Rect(
            UI_WIDTH + (col * CELL_WIDTH) + CELL_WIDTH * 0.1,
            row * CELL_HEIGHT + CELL_HEIGHT * 0.1,
            CELL_WIDTH * 0.8,
            CELL_HEIGHT * 0.8
        )
        self.image = pygame.Surface((self.rect.width, self.rect.height))
        self.image.fill(PLANT_TYPES[plant_type]['color'])

    def update(self, *args, **kwargs):
        if self.health <= 0:
            self.kill()

class Sunflower(Plant):
    def __init__(self, row, col):
        super().__init__('sunflower', row, col)
        self.sun_timer = pygame.time.get_ticks()
        self.sun_interval = 6000 # 6 seconds

    def update(self, sun_group):
        super().update()
        now = pygame.time.get_ticks()
        if now - self.sun_timer > self.sun_interval:
            self.sun_timer = now
            # Spawn sun at plant's location
            sun_group.add(Sun(self.rect.centerx, self.rect.top))

class Shooter(Plant):
    def __init__(self, row, col):
        super().__init__('shooter', row, col)
        self.shoot_timer = pygame.time.get_ticks()
        self.shoot_interval = 2000 # 2 seconds

    def update(self, projectile_group, monster_group):
        super().update()
        
        # Check if a monster is in this row
        monster_in_row = False
        for monster in monster_group:
            if monster.row == self.row:
                monster_in_row = True
                break
        
        if not monster_in_row:
            return

        now = pygame.time.get_ticks()
        if now - self.shoot_timer > self.shoot_interval:
            self.shoot_timer = now
            projectile_group.add(Projectile(self.row, self.rect.right, self.rect.centery))

class Monster(pygame.sprite.Sprite):
    def __init__(self, row):
        super().__init__()
        self.row = row
        self.monster_type = MONSTER_TYPES['walker']
        self.health = self.monster_type['health']
        self.speed = self.monster_type['speed']
        self.damage = self.monster_type['damage']
        
        self.rect = pygame.Rect(
            SCREEN_WIDTH - CELL_WIDTH * 0.5,
            row * CELL_HEIGHT + CELL_HEIGHT * 0.1,
            CELL_WIDTH * 0.8,
            CELL_HEIGHT * 0.8
        )
        self.image = pygame.Surface((self.rect.width, self.rect.height))
        self.image.fill(self.monster_type['color'])
        
        self.is_eating = False
        self.eating_plant = None

    def update(self, plant_group):
        if self.health <= 0:
            self.kill()
            return
            
        # Check for plant collisions
        self.is_eating = False
        self.eating_plant = None
        for plant in plant_group:
            if plant.row == self.row and self.rect.colliderect(plant.rect):
                # Check pixel-perfect distance
                if self.rect.left - plant.rect.right < 5:
                    self.is_eating = True
                    self.eating_plant = plant
                    break

        if self.is_eating:
            # Deal damage to plant
            self.eating_plant.health -= self.damage / FPS
        else:
            # Move left
            self.rect.x -= self.speed

        # Check if game over
        if self.rect.left < UI_WIDTH:
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'type': 'GAME_OVER'}))

class Projectile(pygame.sprite.Sprite):
    def __init__(self, row, x, y):
        super().__init__()
        self.row = row
        self.speed = 5
        self.damage = 25
        
        self.rect = pygame.Rect(x, y - 5, 20, 10)
        self.image = pygame.Surface((self.rect.width, self.rect.height))
        self.image.fill(COLOR_PROJECTILE)

    def update(self, monster_group):
        self.rect.x += self.speed
        
        # Check for collision
        hit_monster = pygame.sprite.spritecollideany(self, monster_group)
        if hit_monster and hit_monster.row == self.row:
            hit_monster.health -= self.damage
            self.kill()

        # Remove if off-screen
        if self.rect.left > SCREEN_WIDTH:
            self.kill()

class Sun(pygame.sprite.Sprite):
    def __init__(self, x=None, y=None):
        super().__init__()
        self.is_falling = (x is None)
        
        if self.is_falling:
            self.rect = pygame.Rect(random.randint(UI_WIDTH, SCREEN_WIDTH - 40), -40, 40, 40)
            self.fall_speed = random.randint(1, 3)
            self.target_y = random.randint(0, SCREEN_HEIGHT - 40)
        else:
            # Spawned by sunflower
            self.rect = pygame.Rect(x - 20, y, 40, 40)
            self.fall_speed = 0
            self.target_y = y + random.randint(10, 30)

        self.image = pygame.Surface((self.rect.width, self.rect.height))
        self.image.fill(COLOR_SUN)
        
        self.despawn_timer = pygame.time.get_ticks()
        self.despawn_time = 8000 # 8 seconds

    def update(self):
        if self.rect.y < self.target_y:
            self.rect.y += self.fall_speed
            
        # Despawn
        if pygame.time.get_ticks() - self.despawn_timer > self.despawn_time:
            self.kill()

# --- Main Game Class ---

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Plant Tower Defense - Pygame")
        self.clock = pygame.time.Clock()
        
        # Game state
        self.running = True
        self.game_over = False
        self.game_won = False # Not implemented yet
        self.sun = 50
        self.score = 0
        self.level = 1
        
        # Plant selection
        self.selected_plant = None
        self.plant_cards = {}
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        
        # Timers
        self.sun_spawn_timer = pygame.time.get_ticks()
        self.sun_spawn_interval = 5000 # 5 seconds
        self.monster_spawn_timer = pygame.time.get_ticks()
        self.monster_spawn_interval = 10000 # 10 seconds
        
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.plant_group = pygame.sprite.Group()
        self.monster_group = pygame.sprite.Group()
        self.projectile_group = pygame.sprite.Group()
        self.sun_group = pygame.sprite.Group()
        
        self.setup_ui()

    def setup_ui(self):
        y_offset = 120
        for plant_type, data in PLANT_TYPES.items():
            card_rect = pygame.Rect(10, y_offset, UI_WIDTH - 20, 80)
            self.plant_cards[plant_type] = {
                'rect': card_rect,
                'data': data
            }
            y_offset += 90

    def run(self):
        while self.running:
            self.handle_events()
            if not self.game_over:
                self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # --- FIX: Correctly check for custom event attribute ---
            if event.type == pygame.USEREVENT:
                if event.dict.get('type') == 'GAME_OVER':
                    self.game_over = True
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game_over:
                    self.restart_game()
                    return
                
                pos = event.pos
                
                # 1. Check for Sun click
                clicked_sun = False
                for sun in self.sun_group:
                    if sun.rect.collidepoint(pos):
                        self.sun += 25
                        sun.kill()
                        clicked_sun = True
                        break # Stop after clicking one sun
                
                if clicked_sun:
                    continue # Don't process other clicks if sun was clicked
                        
                # 2. Check for UI card click
                clicked_card = False
                for plant_type, card in self.plant_cards.items():
                    if card['rect'].collidepoint(pos):
                        if self.sun >= card['data']['cost']:
                            self.selected_plant = plant_type
                        else:
                            self.selected_plant = None
                        clicked_card = True
                        break # Stop after clicking one card
                
                if clicked_card:
                    continue # Don't process grid click if card was clicked
                
                # 3. Check for Grid click
                if pos[0] > UI_WIDTH and self.selected_plant:
                    # --- FIX: Cast col and row to int() ---
                    # This prevents the "TypeError: list indices must be integers"
                    col = int((pos[0] - UI_WIDTH) // CELL_WIDTH)
                    row = int(pos[1] // CELL_HEIGHT)
                    
                    # Boundary check to prevent potential index errors
                    if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
                        # Check if cell is empty
                        if self.grid[row][col] is None:
                            self.plant_new(row, col)

    def plant_new(self, row, col):
        plant_type = self.selected_plant
        cost = PLANT_TYPES[plant_type]['cost']
        
        if self.sun >= cost:
            self.sun -= cost
            
            if plant_type == 'sunflower':
                new_plant = Sunflower(row, col)
            elif plant_type == 'shooter':
                new_plant = Shooter(row, col)
            else:
                return
                
            self.plant_group.add(new_plant)
            self.all_sprites.add(new_plant)
            self.grid[row][col] = new_plant
            self.selected_plant = None
            
    def restart_game(self):
        # Reset all game state
        self.game_over = False
        self.sun = 50
        self.score = 0
        self.level = 1
        self.grid = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        
        # Clear all sprites
        self.all_sprites.empty()
        self.plant_group.empty()
        self.monster_group.empty()
        self.projectile_group.empty()
        self.sun_group.empty()
        
        # Reset timers
        self.sun_spawn_timer = pygame.time.get_ticks()
        self.monster_spawn_timer = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        
        # Spawn falling sun
        if now - self.sun_spawn_timer > self.sun_spawn_interval:
            self.sun_spawn_timer = now
            new_sun = Sun()
            self.sun_group.add(new_sun)
            self.all_sprites.add(new_sun)
            
        # Spawn monster
        if now - self.monster_spawn_timer > self.monster_spawn_interval:
            self.monster_spawn_timer = now
            row = random.randint(0, GRID_ROWS - 1)
            new_monster = Monster(row)
            self.monster_group.add(new_monster)
            self.all_sprites.add(new_monster)
            
        # Update sprite groups
        self.sun_group.update()
        # Pass sun_group for sunflowers
        self.plant_group.update(self.sun_group) 
        self.projectile_group.update(self.monster_group)
        self.monster_group.update(self.plant_group)
        
        # Specific updates for Shooters
        # We need to do this separately because update has different args
        for plant in self.plant_group:
            if isinstance(plant, Shooter):
                plant.update(self.projectile_group, self.monster_group)
            
        # Check for dead plants and update grid
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid[r][c] and not self.grid[r][c].alive():
                    self.grid[r][c] = None

    def draw(self):
        # Draw background
        self.screen.fill(COLOR_BACKGROUND)
        
        # Draw game grid
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                rect = pygame.Rect(UI_WIDTH + c * CELL_WIDTH, r * CELL_HEIGHT, CELL_WIDTH, CELL_HEIGHT)
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)
                
        # Draw all sprites
        self.all_sprites.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
        
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip()

    def draw_ui(self):
        # UI Background
        pygame.draw.rect(self.screen, COLOR_UI, (0, 0, UI_WIDTH, SCREEN_HEIGHT))
        
        # Sun Counter
        sun_text = FONT.render(f"☀️ {self.sun}", True, COLOR_TEXT)
        self.screen.blit(sun_text, (20, 20))
        
        # Plant Cards
        for plant_type, card in self.plant_cards.items():
            rect = card['rect']
            data = card['data']
            
            # Check if affordable
            affordable = self.sun >= data['cost']
            
            # Draw card background
            card_color = (100, 100, 100)
            if affordable:
                card_color = COLOR_TEXT

            if self.selected_plant == plant_type:
                pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, rect)
                pygame.draw.rect(self.screen, (0,0,0), rect, 2) # Border
            else:
                pygame.draw.rect(self.screen, card_color, rect, 2)
            
            # Draw plant representation
            plant_rect_color = data['color']
            if not affordable:
                # Darken color if not affordable
                plant_rect_color = (max(0, data['color'][0]-100), max(0, data['color'][1]-100), max(0, data['color'][2]-100))
                
            pygame.draw.rect(self.screen, plant_rect_color, (rect.x + 10, rect.y + 10, 40, 40))
            
            # Draw text
            name_text = FONT_SMALL.render(data['name'], True, card_color)
            cost_text = FONT_SMALL.render(f"Cost: {data['cost']}", True, card_color)
            self.screen.blit(name_text, (rect.x + 60, rect.y + 10))
            self.screen.blit(cost_text, (rect.x + 60, rect.y + 30))

    def draw_game_over(self):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        
        text = FONT.render("MONSTERS ATE YOU!", True, COLOR_MONSTER)
        text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
        self.screen.blit(text, text_rect)
        
        sub_text = FONT.render("Click to Restart", True, COLOR_TEXT)
        sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20))
        self.screen.blit(sub_text, sub_rect)

# --- Main Execution ---
if __name__ == "__main__":
    game = Game()
    game.run()
