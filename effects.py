import math
import random
import pygame


def casino_font(size, bold=True):
    try:
        font = pygame.font.SysFont("Georgia", size, bold=bold)
        if font is not None:
            return font
    except Exception:
        pass
    return pygame.font.Font(None, size)


def lighten_color(color, amount=30):
    red, green, blue = color
    return (min(red + amount, 255), min(green + amount, 255), min(blue + amount, 255))


def darken_color(color, amount=40):
    red, green, blue = color
    return (max(red - amount, 0), max(green - amount, 0), max(blue - amount, 0))


GRADIENT_TOP = (10, 8, 14)
GRADIENT_BOTTOM = (48, 16, 78)


def build_gradient_background(width, height, top_color=GRADIENT_TOP, bottom_color=GRADIENT_BOTTOM):
    surface = pygame.Surface((width, height))
    height = max(1, height)
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    return surface


def draw_text_shadow(surface, font, text, color, center, shadow_offset=(3, 3), shadow_alpha=140):
    shadow_surf = font.render(text, True, (0, 0, 0))
    shadow_surf.set_alpha(shadow_alpha)
    shadow_rect = shadow_surf.get_rect(
        center=(center[0] + shadow_offset[0], center[1] + shadow_offset[1])
    )
    surface.blit(shadow_surf, shadow_rect)

    main_surf = font.render(text, True, color)
    main_rect = main_surf.get_rect(center=center)
    surface.blit(main_surf, main_rect)
    return main_rect


def build_rounded_gradient(size, top_color, bottom_color, radius):
    width, height = size
    width = max(1, width)
    height = max(1, height)

    gradient = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        t = y / max(1, height - 1)
        dither = 0.5 if (y % 2 == 0) else -0.5
        r = min(255, max(0, round(top_color[0] + (bottom_color[0] - top_color[0]) * t + dither)))
        g = min(255, max(0, round(top_color[1] + (bottom_color[1] - top_color[1]) * t + dither)))
        b = min(255, max(0, round(top_color[2] + (bottom_color[2] - top_color[2]) * t + dither)))
        pygame.draw.line(gradient, (r, g, b, 255), (0, y), (width, y))

    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return gradient


_click_flashes = {}
CLICK_FLASH_DURATION_MS = 160


def register_click_flash(key):
    _click_flashes[key] = pygame.time.get_ticks()


def is_click_flashing(key):
    started = _click_flashes.get(key)
    if started is None:
        return False
    if pygame.time.get_ticks() - started < CLICK_FLASH_DURATION_MS:
        return True
    del _click_flashes[key]
    return False


def draw_button(surface, rect, text, font, base_color, mouse_pos, key=None,
                 text_color=(255, 255, 255), radius=14, hover_grow=8):
    hover = rect.collidepoint(mouse_pos)
    clicked = key is not None and is_click_flashing(key)

    display_rect = rect.inflate(hover_grow, hover_grow) if hover else rect.copy()
    display_rect.center = rect.center

    if clicked:
        light = lighten_color(base_color, 90)
        dark = lighten_color(base_color, 45)
    else:
        light = lighten_color(base_color, 50)
        dark = darken_color(base_color, 55)

    shadow_surf = pygame.Surface(display_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 100), shadow_surf.get_rect(), border_radius=radius)
    surface.blit(shadow_surf, (display_rect.x, display_rect.y + 4))

    gradient = build_rounded_gradient(display_rect.size, light, dark, radius)
    surface.blit(gradient, display_rect.topleft)

    outline_color = darken_color(base_color, 70)
    pygame.draw.rect(surface, outline_color, display_rect, width=5, border_radius=radius)

    label_surf = font.render(text, True, text_color)
    surface.blit(label_surf, label_surf.get_rect(center=display_rect.center))
    return hover


HEART_PIXEL_PATTERN = [
    "0110110",
    "1111111",
    "1111111",
    "0111110",
    "0011100",
    "0001000",
]


def draw_heart_icon(surface, center, color, pixel_size=4):
    rows = len(HEART_PIXEL_PATTERN)
    cols = len(HEART_PIXEL_PATTERN[0])
    total_w = cols * pixel_size
    total_h = rows * pixel_size
    start_x = center[0] - total_w // 2
    start_y = center[1] - total_h // 2

    for row_index, row in enumerate(HEART_PIXEL_PATTERN):
        for col_index, cell in enumerate(row):
            if cell == "1":
                pixel_rect = pygame.Rect(
                    start_x + col_index * pixel_size,
                    start_y + row_index * pixel_size,
                    pixel_size, pixel_size,
                )
                pygame.draw.rect(surface, color, pixel_rect)

    return total_w, total_h


PANEL_BORDER = (35, 14, 62)
PANEL_HEADER = (150, 80, 210)
PANEL_BODY_TOP = (18, 10, 26)
PANEL_BODY_BOTTOM = (108, 44, 178)

PILL_TOP = (96, 44, 158)
PILL_BOTTOM = (44, 16, 78)
PILL_CLICKED_TOP = (150, 90, 220)
PILL_CLICKED_BOTTOM = (90, 40, 160)
PILL_BORDER = (176, 132, 226)


def draw_panel(surface, rect, title_text, title_font, header_color=PANEL_HEADER, show_header=True):
    pygame.draw.rect(surface, PANEL_BORDER, rect, border_radius=26)

    inner = rect.inflate(-10, -10)
    body_gradient = build_rounded_gradient(inner.size, PANEL_BODY_TOP, PANEL_BODY_BOTTOM, 20)
    surface.blit(body_gradient, inner.topleft)

    if show_header:
        header_rect = pygame.Rect(0, 0, int(inner.width * 0.78), 56)
        header_rect.centerx = inner.centerx
        header_rect.top = rect.top - 18
        pygame.draw.rect(surface, header_color, header_rect, border_radius=18)
        pygame.draw.rect(surface, PANEL_BORDER, header_rect, width=4, border_radius=18)

        title_surf = title_font.render(title_text, True, (255, 255, 255))
        surface.blit(title_surf, title_surf.get_rect(center=header_rect.center))


def draw_pill_button(surface, rect, text, font, mouse_pos, key=None, text_color=(255, 255, 255)):
    hover = rect.collidepoint(mouse_pos)
    clicked = key is not None and is_click_flashing(key)

    display_rect = rect.inflate(8, 8) if hover else rect.copy()
    display_rect.center = rect.center
    radius = display_rect.height // 2

    if clicked:
        top_color, bottom_color = PILL_CLICKED_TOP, PILL_CLICKED_BOTTOM
    else:
        top_color, bottom_color = PILL_TOP, PILL_BOTTOM

    shadow_surf = pygame.Surface(display_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 90), shadow_surf.get_rect(), border_radius=radius)
    surface.blit(shadow_surf, (display_rect.x, display_rect.y + 3))

    gradient = build_rounded_gradient(display_rect.size, top_color, bottom_color, radius)
    surface.blit(gradient, display_rect.topleft)

    pygame.draw.rect(surface, PILL_BORDER, display_rect, width=3, border_radius=radius)

    label_surf = font.render(text, True, text_color)
    surface.blit(label_surf, label_surf.get_rect(center=display_rect.center))
    return hover


def draw_close_button(surface, center, radius, mouse_pos, key=None):
    hit_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    hit_rect.center = center
    hover = hit_rect.collidepoint(mouse_pos)
    clicked = key is not None and is_click_flashing(key)

    display_radius = radius + (4 if hover else 0)
    fill_color = (215, 95, 115) if clicked else (150, 70, 190)

    pygame.draw.circle(surface, PANEL_BORDER, center, display_radius + 4)
    pygame.draw.circle(surface, fill_color, center, display_radius)

    offset = display_radius * 0.4
    pygame.draw.line(
        surface, (255, 255, 255),
        (center[0] - offset, center[1] - offset), (center[0] + offset, center[1] + offset), 4,
    )
    pygame.draw.line(
        surface, (255, 255, 255),
        (center[0] - offset, center[1] + offset), (center[0] + offset, center[1] - offset), 4,
    )
    return hover


def draw_star(surface, center, size, color=(255, 196, 40), outline_color=(150, 100, 10)):
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        point_radius = size if i % 2 == 0 else size * 0.45
        x = center[0] + point_radius * math.cos(angle)
        y = center[1] - point_radius * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, outline_color, points, width=2)


class ScreenShake:

    def __init__(self):
        self.trauma = 0.0

    def add_trauma(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt):
        if self.trauma > 0:
            self.trauma = max(0.0, self.trauma - dt * 0.0018)

    def get_offset(self):
        if self.trauma <= 0:
            return (0, 0)
        power = self.trauma * self.trauma
        max_offset = 30
        reach = int(max_offset * power)
        if reach <= 0:
            return (0, 0)
        return (random.randint(-reach, reach), random.randint(-reach, reach))


class Particle:

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3.2, 3.2)
        self.vy = random.uniform(-5.5, -1.5)
        self.life = random.uniform(400, 700)
        self.age = 0
        self.color = color
        self.size = random.randint(3, 6)

    def update(self, dt):
        self.age += dt
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.18

    def is_dead(self):
        return self.age >= self.life

    def draw(self, surface):
        progress = min(1.0, self.age / self.life)
        alpha = max(0, int(255 * (1 - progress)))
        size = max(1, self.size)
        particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            particle_surf, (*self.color, alpha), (size, size), size
        )
        surface.blit(particle_surf, (self.x - size, self.y - size))


class ParticleSystem:

    def __init__(self):
        self.particles = []

    def burst(self, x, y, colors, count=16):
        for _ in range(count):
            color = random.choice(colors)
            self.particles.append(Particle(x, y, color))

    def update(self, dt):
        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if not p.is_dead()]

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)


class FallingCard:

    def __init__(self, image, screen_w, screen_h):
        self.image = image
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.reset(initial=True)

    def reset(self, initial=False):
        self.x = random.randint(0, self.screen_w)
        if initial:
            self.y = random.randint(-self.screen_h, self.screen_h)
        else:
            self.y = random.randint(-200, -20)
        self.speed = random.uniform(1.2, 3.4)
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-1.5, 1.5)

    def update(self):
        self.y += self.speed
        self.angle += self.spin
        if self.y > self.screen_h + 100:
            self.reset()

    def draw(self, surface):
        rotated = pygame.transform.rotate(self.image, self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        surface.blit(rotated, rect)


class FallingCardsBackground:

    def __init__(self, image, screen_w, screen_h, count=16):
        scaled = pygame.transform.smoothscale(
            image, (int(image.get_width() * 0.6), int(image.get_height() * 0.6))
        )
        self.cards = [FallingCard(scaled, screen_w, screen_h) for _ in range(count)]

    def update(self):
        for card in self.cards:
            card.update()

    def draw(self, surface):
        for card in self.cards:
            card.draw(surface)