import pygame
import os
import sys


# Init
pygame.init()

WIDTH = 1000
HEIGHT = 800
screen = pygame.display.set_mode([WIDTH, HEIGHT])

fps = 60

gravity = 0.5
bounce_stop = 0.3  # To prevent infinity bouncing

resist = 0.07
rubbing_stop = 0.05

timer = pygame.time.Clock()

# Classes and funcs

def get_sign(a):
    if a > 0:
        return 1

    if a < 0:
        return -1

    return 0

def load_image(name, colorkey=None):
    fullname = os.path.join('assets', name)

    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()

    image = pygame.image.load(fullname)
    return image

class Player(pygame.sprite.Sprite):
    image1 = load_image('baller1.png')
    image2 = load_image('baller2.png')

    def __init__(self, *group, x_pos=0, y_pos=0):
        super().__init__(*group)
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.has_ball = False
        self.image = Player.image1
        self.rect = self.image.get_rect()
        self.wait = 0

    def catch_ball(self):
        self.has_ball = True
        self.image = Player.image2
        self.rect = self.image.get_rect().move(self.rect.x, self.rect.y)

    def loose_ball(self):
        self.has_ball = False
        self.wait = 100
        self.image = Player.image1
        self.rect = self.image.get_rect().move(self.rect.x, self.rect.y)

    def through(self, mouse_pos, ball):
        if self.has_ball:
            self.loose_ball()
            ball.release(self)
            ball.through(mouse_pos)

    def move(self, x, y):
        self.x_pos += x
        self.y_pos += y

    def update(self):
        if self.wait:
            self.wait -= 1

        self.rect.x = self.x_pos
        self.rect.y = self.y_pos


class Ball(pygame.sprite.Sprite):
    image = load_image('ball.png')

    def __init__(self, *group, x_pos=0, y_pos=0, mass=1, x_speed=0, y_speed=0, angle=0, retention=0.7):
        super().__init__(*group)
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.mass = mass
        self.image = Ball.image
        self.radius = self.image.get_rect()[3]
        self.rect = self.image.get_rect()
        self.x_speed = x_speed
        self.y_speed = y_speed
        self.angle = angle
        self.retention = retention  # Bouncing coef
        self.catched = False

    def release(self, person):
        self.pos_x = person.rect.centerx
        self.pos_y = person.rect.centery

        self.x_speed = 0
        self.y_speed = 0

        self.catched = False

    def check_gravity(self):
        if self.y_pos < HEIGHT - self.radius:
            self.y_speed += gravity  # Flying check
        else:
            if self.y_speed > bounce_stop:
                self.y_speed *= -1 * self.retention  # Bouncing
            else:
                if abs(self.y_speed) <= bounce_stop:  # Stop bouncing check
                    self.y_speed = 0

    def check_borders(self):
        if self.x_pos <= 0 or self.x_pos >= WIDTH - self.radius:
            self.x_speed *= -1
            return

        if abs(self.x_speed) <= rubbing_stop:
            self.x_speed = 0

        self.x_speed -= get_sign(self.x_speed) * resist

    def through(self, mouse_pos):
        if self.y_speed or self.x_speed or self.catched:
            return

        self.y_speed = (mouse_pos[1] - self.y_pos) / 15
        self.x_speed = (mouse_pos[0] - self.x_pos) / 15

    def catched_check(self, player):
        if self.rect.colliderect(player.rect) and not player.wait:
            self.catched = True
            return True

    def update(self):
        if self.catched:
            return

        # Update vars
        self.check_gravity()
        self.check_borders()

        # Move ball
        self.x_pos += self.x_speed
        self.y_pos += self.y_speed

        # Move rectangle
        self.rect.x = self.x_pos
        self.rect.y = self.y_pos


# Post init
balls = pygame.sprite.Group()

ball = Ball(balls, x_pos = WIDTH-200, y_pos = HEIGHT-40)

persons = pygame.sprite.Group()

player = Player(persons, x_pos=WIDTH-168, y_pos=HEIGHT-168)

# Loop
run = True

while run:
    screen.fill('white')

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            x, y = 0, 0
            if event.key == pygame.K_LEFT:
                x -= 1
            if event.key == pygame.K_RIGHT:
                x += 1
            if event.key == pygame.K_DOWN:
                y += 1
            if event.key == pygame.K_UP:
                y -= 1

            player.move(x* 10, y * 10)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                ball.through(event.pos)
                player.through(event.pos, ball)



    if ball.catched_check(player):
        player.catch_ball()

    if not ball.catched:
        balls.update()
        balls.draw(screen)

    persons.draw(screen)
    persons.update()

    pygame.display.flip()
    timer.tick(fps)


pygame.quit()

