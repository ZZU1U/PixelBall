import pygame
import os
import sys

# Init
pygame.init()

WIDTH = 1000
HEIGHT = 800

bottom_line = 10
side_lines = 30

screen = pygame.display.set_mode([WIDTH, HEIGHT])

fps = 60

gravity = 0.5
bounce_stop = 0.3  # To prevent infinity bouncing

resist = 0.07
rubbing_stop = 0.05

timer = pygame.time.Clock()


# Classes and funcs

def get_sign(a: int) -> int:
    if a > 0:
        return 1

    if a < 0:
        return -1

    return 0


def load_image(name: str) -> pygame.Surface:
    fullname = os.path.join('assets', name)

    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()

    image = pygame.image.load(fullname)
    return image


class Player(pygame.sprite.Sprite):
    with_ball_num = 15
    without_ball_num = 1

    with_ball_img = [load_image(f'baller_with_ball/baller_stand{i}.png') for i in range(with_ball_num)]
    without_ball_img = [load_image(f'baller_without_ball/baller_stand{i}.png') for i in range(without_ball_num)]

    x_boost = 3
    max_x_speed = x_boost * 8

    y_jump_speed = -15

    def __init__(self, *group, x_pos=0, y_pos=0):
        super().__init__(*group)
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.x_speed = 0
        self.y_speed = 0
        self.y_boost = 0
        self.x_boost = 0
        self.last_move = 'r'
        self.has_ball = None
        self.image_num = 0
        self.image = Player.with_ball_img[self.image_num]
        self.rect = self.image.get_rect()
        self.wait = 0

    def catch_ball(self, ball):
        self.has_ball = ball
        ball.catched = True
        ball.rect = ball.rect.move(self.x_pos, self.y_pos)
        self.rect = self.image.get_rect().move(self.rect.x, self.rect.y)

    def loose_ball(self):
        self.has_ball = None
        self.wait = 100
        self.rect = self.image.get_rect().move(self.rect.x, self.rect.y)

    def throw(self, mouse_pos, ball):
        if self.has_ball is not None:
            self.loose_ball()
            ball.release(self.rect)
            ball.throw(mouse_pos)

    def jump(self):
        self.y_speed = Player.y_jump_speed
        self.y_boost = gravity

    def move(self, dx: int, dy: int):
        if dx > 0 and not self.y_boost:
            self.x_boost = Player.x_boost
            self.last_move = 'r'
        if dx < 0 and not self.y_boost:
            self.x_boost = -Player.x_boost
            self.last_move = 'l'

        if dx == 0 or self.y_boost:
            self.x_boost = Player.x_boost * get_sign(self.x_speed) * -1

        if dy and not self.y_boost:
            self.jump()

    def x_check(self):
        if self.x_pos < side_lines:
            self.x_pos = side_lines
            self.x_speed = 0
            self.x_boost = 0

        if self.x_pos > WIDTH - side_lines - self.rect[2]:
            self.x_pos = WIDTH - side_lines - self.rect[2]
            self.x_speed = 0
            self.x_boost = 0

    def y_check(self):
        if self.y_pos > HEIGHT - bottom_line - self.rect[3]:
            self.y_speed = 0
            self.y_pos = HEIGHT - bottom_line - self.rect[3]
            return True

        return False

    def update(self):
        if self.wait:
            self.wait -= 1

        self.image_num += 1

        self.x_speed += self.x_boost

        if self.x_speed < -Player.max_x_speed:
            self.x_speed = -Player.max_x_speed
            self.x_boost = 0

        if self.x_speed > Player.max_x_speed:
            self.x_speed = Player.max_x_speed
            self.x_boost = 0

        self.y_pos += self.y_speed
        self.x_pos += self.x_speed

        self.y_speed += self.y_boost

        self.x_check()

        if self.y_check():
            self.y_boost = 0

        if self.has_ball:
            self.image_num %= Player.with_ball_num
            if self.last_move == 'l':
                self.image = Player.with_ball_img[self.image_num]
            else:
                self.image = pygame.transform.flip(Player.with_ball_img[self.image_num], True, False)

        else:
            self.image_num %= Player.without_ball_num
            if self.last_move == 'l':
                self.image = Player.without_ball_img[self.image_num]
            else:
                self.image = pygame.transform.flip(Player.without_ball_img[self.image_num], True, False)

        self.rect.x = self.x_pos
        self.rect.y = self.y_pos


class Hoop:
    def __init__(self, x_pos, y_pos, width, height, color):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.width = width
        self.height = height
        self.color = color

    def does_touch(self, rect: pygame.Rect):
        return (rect.colliderect(pygame.Rect(self.x_pos + self.width - 1, self.y_pos, 1, self.height)) or
                rect.colliderect(pygame.Rect(self.x_pos - 1, self.y_pos, 1, self.height)))

    def draw(self, game_screen):
        pygame.draw.rect(game_screen, self.color, (self.x_pos, self.y_pos, self.width, self.height))

    def is_score(self, rect: pygame.Rect):
        return rect.colliderect(pygame.Rect(self.x_pos, self.y_pos, self.width, self.height)) and not self.does_touch(rect)


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

    def bounce_off(self):
        self.x_speed *= -1
        self.y_speed *= -1

    def release(self, person_rect: pygame.Rect):
        self.x_pos = person_rect.centerx
        self.y_pos = person_rect.centery

        self.x_speed = 0
        self.y_speed = 0

        self.catched = False

    def check_gravity(self):
        if self.y_pos < HEIGHT - self.radius - bottom_line:
            self.y_speed += gravity  # Flying check
        else:
            if self.y_speed > bounce_stop:
                self.y_speed *= -1 * self.retention  # Bouncing
            else:
                if abs(self.y_speed) <= bounce_stop:  # Stop bouncing check
                    self.y_speed = 0

    def check_borders(self):
        if self.x_pos < side_lines:
            self.x_pos = side_lines
            self.x_speed *= -1
            return

        if self.x_pos > WIDTH - self.radius - side_lines:
            self.x_pos = WIDTH - self.radius - side_lines
            self.x_speed *= -1
            return

        if abs(self.x_speed) <= rubbing_stop:
            self.x_speed = 0

        self.x_speed -= get_sign(self.x_speed) * resist

    def throw(self, mouse_pos: tuple[int]):
        if self.y_speed or self.x_speed or self.catched:
            return

        coef = ((mouse_pos[1] - self.y_pos) ** 2 + (mouse_pos[0] - self.x_pos) ** 2) ** 0.5

        self.y_speed = (mouse_pos[1] - self.y_pos) / coef * 25
        self.x_speed = (mouse_pos[0] - self.x_pos) / coef * 25

    def catched_check(self, thrower: Player):
        if self.rect.colliderect(thrower.rect) and not thrower.wait:
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

game_ball = Ball(balls, x_pos=WIDTH - 200, y_pos=HEIGHT - 40)

persons = pygame.sprite.Group()

player = Player(persons, x_pos=WIDTH - 168, y_pos=HEIGHT - 168)

left_hoop = Hoop(10, HEIGHT - 500 - 20, 200, 20, (255, 0, 0))
right_hoop = Hoop(WIDTH - 10 - 200, HEIGHT - 500 - 20, 200, 20, (0, 0, 255))

my_font = pygame.font.SysFont('Comic Sans MS', 30)

court_img = load_image('court.png')

left_score = 0

right_score = 0

# Loop
run = True

x, y = 0, 0

while run:
    screen.blit(court_img, (0, 0))

    game = my_font.render(f'{left_score} : {right_score}', False, (
                                 (left_score > right_score) * 255,
                                 (left_score == right_score) * 255,
                                 (left_score < right_score) * 255))

    screen.blit(game, (0, 0))

    left_hoop.draw(screen)
    right_hoop.draw(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_LEFT, pygame.K_a]:
                x = -1
            if event.key in [pygame.K_RIGHT, pygame.K_d]:
                x = 1
            if event.key in [pygame.K_UP, pygame.K_w, pygame.K_SPACE]:
                y = 1

        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d]:
                x = 0

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                game_ball.throw(event.pos)
                player.throw(event.pos, game_ball)

    player.move(x, y)
    y = 0

    if left_hoop.does_touch(game_ball.rect) or right_hoop.does_touch(game_ball.rect):
        game_ball.bounce_off()

    if game_ball.catched_check(player):
        player.catch_ball(game_ball)

    if not game_ball.catched:
        balls.update()
        balls.draw(screen)

    if left_hoop.is_score(game_ball.rect):
        player.catch_ball(game_ball)
        right_score += 1
        print(f'{left_score} : {right_score}')

    if right_hoop.is_score(game_ball.rect):
        player.catch_ball(game_ball)
        left_score += 1
        print(f'{left_score} : {right_score}')

    persons.draw(screen)
    persons.update()

    pygame.display.flip()
    timer.tick(fps)

pygame.quit()
