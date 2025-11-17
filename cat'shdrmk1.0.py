import pygame
import time
import random

pygame.init()

gray = (119, 118, 110)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 200, 0)
blue = (0, 0, 200)
bright_red = (255, 0, 0)
bright_green = (0, 255, 0)
bright_blue = (0, 0, 255)
white = (255, 255, 255)
yellow = (255, 255, 0)

display_width = 600
display_height = 400
gamedisplays = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption("Cat's Mario Kart 1 Tour")
clock = pygame.time.Clock()

car_width = 50
car_height = 100
obs_width = 50
obs_height = 100

# Road boundaries
road_left_boundary = 100
road_right_boundary = 500

raceway = 0

def text_objects(text, font):
    textsurface = font.render(text, True, black)
    return textsurface, textsurface.get_rect()

def message_display(text):
    largetext = pygame.font.Font("freesansbold.ttf", 80)
    textsurf, textrect = text_objects(text, largetext)
    textrect.center = ((display_width/2), (display_height/2))
    gamedisplays.blit(textsurf, textrect)
    pygame.display.update()
    time.sleep(3)
    intro_loop()

def crash():
    message_display("YOU CRASHED")

def button(msg, x, y, w, h, ic, ac, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(gamedisplays, ac, (x, y, w, h))
        if click[0] == 1 and action is not None:
            if action == "play":
                select_raceway()
            elif action == "quit":
                pygame.quit()
                quit()
            elif action == "race1":
                global raceway
                raceway = 1
                countdown()
            elif action == "race2":
                raceway = 2
                countdown()
            elif action == "race3":
                raceway = 3
                countdown()
    else:
        pygame.draw.rect(gamedisplays, ic, (x, y, w, h))
    smalltext = pygame.font.Font("freesansbold.ttf", 20)
    textsurf, textrect = text_objects(msg, smalltext)
    textrect.center = ((x + (w / 2)), (y + (h / 2)))
    gamedisplays.blit(textsurf, textrect)

def intro_loop():
    intro = True
    while intro:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        gamedisplays.fill(gray)
        largetext = pygame.font.Font('freesansbold.ttf', 50)
        TextSurf, TextRect = text_objects("Cat's Mario Kart 1 Tour", largetext)
        TextRect.center = (display_width / 2, display_height / 4)
        gamedisplays.blit(TextSurf, TextRect)
        button("START", 150, 300, 100, 50, green, bright_green, "play")
        button("QUIT", 350, 300, 100, 50, red, bright_red, "quit")
        pygame.display.update()
        clock.tick(50)

def select_raceway():
    select = True
    while select:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        gamedisplays.fill(gray)
        largetext = pygame.font.Font('freesansbold.ttf', 50)
        TextSurf, TextRect = text_objects("Choose Raceway", largetext)
        TextRect.center = (display_width / 2, display_height / 4)
        gamedisplays.blit(TextSurf, TextRect)
        button("Raceway 1", 100, 300, 100, 50, green, bright_green, "race1")
        button("Raceway 2", 250, 300, 100, 50, blue, bright_blue, "race2")
        button("Raceway 3", 400, 300, 100, 50, red, bright_red, "race3")
        pygame.display.update()
        clock.tick(50)

def countdown():
    for count in ["3", "2", "1", "GO!!!"]:
        gamedisplays.fill(gray)
        countdown_background()
        largetext = pygame.font.Font('freesansbold.ttf', 115)
        TextSurf, TextRect = text_objects(count, largetext)
        TextRect.center = (display_width / 2, display_height / 2)
        gamedisplays.blit(TextSurf, TextRect)
        pygame.display.update()
        clock.tick(1)
    game_loop()

def countdown_background():
    font = pygame.font.SysFont(None, 25)
    x = (display_width * 0.45)
    y = (display_height * 0.8)
    background(0)
    car(x, y)
    text = font.render("DODGED: 0", True, black)
    score = font.render("SCORE: 0", True, red)
    gamedisplays.blit(text, (0, 50))
    gamedisplays.blit(score, (0, 30))

def background(road_y):
    gamedisplays.fill(green)
    pygame.draw.rect(gamedisplays, gray, (road_left_boundary, 0, road_right_boundary - road_left_boundary, display_height))
    # Animate road lines
    for i in range(-50, display_height + 50, 50):
        pygame.draw.line(gamedisplays, yellow, (300, i + road_y), (300, i + road_y + 25), 5)
        pygame.draw.line(gamedisplays, white, (road_left_boundary, i + road_y), (road_left_boundary, i + road_y + 50), 5)
        pygame.draw.line(gamedisplays, white, (road_right_boundary, i + road_y), (road_right_boundary, i + road_y + 50), 5)

def car(x, y):
    pygame.draw.rect(gamedisplays, red, (x, y, car_width, car_height))
    smalltext = pygame.font.Font("freesansbold.ttf", 20)
    textsurf, textrect = text_objects("Cat", smalltext)
    textrect.center = (x + car_width / 2, y + car_height / 2)
    gamedisplays.blit(textsurf, textrect)

def obstacle(obs_startx, obs_starty, obs):
    pygame.draw.rect(gamedisplays, blue, (obs_startx, obs_starty, obs_width, obs_height))
    smalltext = pygame.font.Font("freesansbold.ttf", 20)
    textsurf, textrect = text_objects("Enemy", smalltext)
    textrect.center = (obs_startx + obs_width / 2, obs_starty + obs_height / 2)
    gamedisplays.blit(textsurf, textrect)

def score_system(passed, score):
    font = pygame.font.SysFont(None, 25)
    text = font.render("DODGED: " + str(passed), True, black)
    sc = font.render("SCORE: " + str(score), True, red)
    gamedisplays.blit(text, (0, 50))
    gamedisplays.blit(sc, (0, 30))

def game_loop():
    x = display_width * 0.45
    y = display_height * 0.8
    x_change = 0
    
    # Obstacle properties
    obs_startx = random.randrange(road_left_boundary, road_right_boundary - obs_width)
    obs_starty = -600
    obs_speed = 7
    
    # Road animation properties
    road_y = 0
    road_speed = 10 # Speed of the road lines
    
    # Scoring
    passed = 0
    score = 0
    
    game_exit = False

    while not game_exit:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            # Car movement events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x_change = -5
                elif event.key == pygame.K_RIGHT:
                    x_change = 5
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    x_change = 0

        # Update car position
        x += x_change

        # Update road animation
        road_y = (road_y + road_speed) % 50 # Loop the 50px line segment
        
        # Draw background (animated)
        background(road_y)

        # Update and draw obstacle
        obs_starty += obs_speed
        obstacle(obs_startx, obs_starty, 0)
        
        # Draw car
        car(x, y)
        
        # Draw score
        score_system(passed, score)

        # Check boundaries
        if x > road_right_boundary - car_width or x < road_left_boundary:
            crash()

        # Check if obstacle is off-screen
        if obs_starty > display_height:
            obs_starty = 0 - obs_height
            obs_startx = random.randrange(road_left_boundary, road_right_boundary - obs_width)
            passed += 1
            score += 10
            # Increase difficulty
            if passed % 5 == 0:
                obs_speed += 1

        # Collision detection
        if y < obs_starty + obs_height and y + car_height > obs_starty:
            if (x > obs_startx and x < obs_startx + obs_width) or \
               (x + car_width > obs_startx and x + car_width < obs_startx + obs_width) or \
               (obs_startx > x and obs_startx < x + car_width) or \
               (obs_startx + obs_width > x and obs_startx + obs_width < x + car_width):
                crash()

        pygame.display.update()
        clock.tick(60)

# Start the game
intro_loop()
