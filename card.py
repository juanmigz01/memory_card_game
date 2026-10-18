import random
import pygame


class Card:

    SHAKE_DURATION_MS = 260
    REMOVE_DURATION_MS = 420
    DEAL_DURATION_MS = 650
    REMOVE_TRAVEL_DISTANCE = 550

    def __init__(self, val, front_img, back_img, x, y):
        self.val = val

        self.front_img = front_img
        self.back_img = back_img

        self.is_flipped = False
        self.is_matched = False

        self.rect = self.front_img.get_rect(topleft=(x, y))

        self.shake_timer = 0
        self.shake_offset = 0

        self.is_removing = False
        self.is_removed = False
        self.remove_elapsed = 0
        self.remove_dx = 0
        self.remove_dy = 0

        self.is_dealing = False
        self.deal_from = (x, y)
        self.deal_to = (x, y)
        self.deal_elapsed = 0

        self.fall_speed = 0.0

    def start_deal(self, from_pos, delay_ms=0):
        self.deal_from = from_pos
        self.deal_to = self.rect.topleft
        self.deal_elapsed = -delay_ms
        self.is_dealing = True
        self.rect.topleft = from_pos

    def update_deal(self, dt):
        if not self.is_dealing:
            return

        self.deal_elapsed += dt
        if self.deal_elapsed < 0:
            return

        progress = min(1.0, self.deal_elapsed / self.DEAL_DURATION_MS)
        eased = 1 - (1 - progress) ** 3

        from_x, from_y = self.deal_from
        to_x, to_y = self.deal_to
        self.rect.x = int(from_x + (to_x - from_x) * eased)
        self.rect.y = int(from_y + (to_y - from_y) * eased)

        if progress >= 1.0:
            self.is_dealing = False

    def update(self, dt):
        self.update_deal(dt)

        if self.shake_timer > 0:
            self.shake_timer -= dt
            self.shake_offset = random.randint(-6, 6) if self.shake_timer > 0 else 0

        if self.is_removing and not self.is_removed:
            self.remove_elapsed += dt
            if self.remove_elapsed >= self.REMOVE_DURATION_MS:
                self.is_removed = True

    def start_shake(self):
        self.shake_timer = self.SHAKE_DURATION_MS

    def start_remove(self):
        self.is_removing = True
        self.remove_elapsed = 0
        direction = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        self.remove_dx, self.remove_dy = direction

    def start_fall(self):
        self.fall_speed = random.uniform(2.0, 4.5)

    def apply_fall(self):
        self.fall_speed += 0.2
        self.rect.y += int(self.fall_speed)
        self.rect.x += random.randint(-1, 1)

    HOVER_SCALE = 1.12

    def draw(self, surface, mouse_pos=None):
        if self.is_removed:
            return

        image = self.front_img if (self.is_flipped or self.is_matched) else self.back_img

        if self.is_removing:
            progress = min(1.0, self.remove_elapsed / self.REMOVE_DURATION_MS)
            traveled = int(self.REMOVE_TRAVEL_DISTANCE * progress)

            draw_rect = self.rect.copy()
            draw_rect.x += self.remove_dx * traveled
            draw_rect.y += self.remove_dy * traveled

            faded_img = image.copy()
            faded_img.set_alpha(int(255 * (1 - progress)))
            surface.blit(faded_img, draw_rect)
            return

        is_hoverable = not self.is_flipped and not self.is_matched and not self.is_removing
        is_hovered = is_hoverable and mouse_pos is not None and self.rect.collidepoint(mouse_pos)

        if is_hovered:
            scaled_w = int(image.get_width() * self.HOVER_SCALE)
            scaled_h = int(image.get_height() * self.HOVER_SCALE)
            scaled_img = pygame.transform.smoothscale(image, (scaled_w, scaled_h))
            draw_rect = scaled_img.get_rect(center=self.rect.center)
            draw_rect.x += self.shake_offset
            surface.blit(scaled_img, draw_rect)
            return

        draw_rect = self.rect.copy()
        draw_rect.x += self.shake_offset
        surface.blit(image, draw_rect)

    def is_clicked(self, mouse_pos):
        if not self.is_flipped and not self.is_matched and not self.is_removing:
            return self.rect.collidepoint(mouse_pos)
        return False

    def flip(self):
        self.is_flipped = not self.is_flipped