import os
import sys
import pygame
from effects import (
    casino_font, build_gradient_background, draw_button, draw_text_shadow, lighten_color,
    register_click_flash,
)

BASE_DIR = os.path.dirname(__file__)

COLOR_BLACK = (12, 10, 16)
COLOR_WHITE = (240, 238, 245)
COLOR_PURPLE = (147, 51, 234)
COLOR_PURPLE_DARK = (88, 28, 135)
COLOR_PURPLE_LIGHT = (196, 156, 255)
COLOR_OFF = (110, 30, 55)
COLOR_LABEL_BOX = (32, 26, 40)

LABEL_WIDTH = 250
TOGGLE_WIDTH = 130
ROW_HEIGHT = 46
ROW_GAP = 12


class DummySound:

    def play(self):
        pass

    def set_volume(self, vol):
        pass


def get_volume_from_mouse(mouse_x, slider_x, slider_width):
    volume = (mouse_x - slider_x) / slider_width

    if volume < 0:
        volume = 0
    if volume > 1:
        volume = 1
    return volume


def draw_volume_slider(screen, track_rect, volume, is_active):
    pygame.draw.rect(screen, (35, 30, 45), track_rect, border_radius=6)

    filled_width = int(track_rect.width * volume)
    if filled_width > 0:
        filled_rect = pygame.Rect(
            track_rect.x, track_rect.y, filled_width, track_rect.height
        )
        fill_color = COLOR_PURPLE_LIGHT if is_active else COLOR_PURPLE
        pygame.draw.rect(screen, fill_color, filled_rect, border_radius=6)

    handle_x = track_rect.x + filled_width
    handle_y = track_rect.centery
    handle_color = COLOR_WHITE if is_active else (210, 205, 215)
    pygame.draw.circle(screen, handle_color, (handle_x, handle_y), 12)

    percent_font = casino_font(24, bold=False)
    percent_text = percent_font.render(f"{int(volume * 100)}%", True, COLOR_WHITE)
    screen.blit(percent_text, (track_rect.right + 16, track_rect.centery - 9))


def draw_setting_row(screen, x, y, label_text, is_on, mouse_pos, label_font, toggle_font):
    label_rect = pygame.Rect(x, y, LABEL_WIDTH, ROW_HEIGHT)
    shadow_surf = pygame.Surface(label_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(), border_radius=8)
    screen.blit(shadow_surf, (label_rect.x, label_rect.y + 3))
    pygame.draw.rect(screen, COLOR_LABEL_BOX, label_rect, border_radius=8)
    label_surf = label_font.render(label_text, True, COLOR_WHITE)
    screen.blit(label_surf, label_surf.get_rect(center=label_rect.center))

    toggle_rect = pygame.Rect(x + LABEL_WIDTH + ROW_GAP, y, TOGGLE_WIDTH, ROW_HEIGHT)
    color = COLOR_PURPLE if is_on else COLOR_OFF
    if toggle_rect.collidepoint(mouse_pos):
        color = lighten_color(color)
    toggle_shadow = pygame.Surface(toggle_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(toggle_shadow, (0, 0, 0, 80), toggle_shadow.get_rect(), border_radius=8)
    screen.blit(toggle_shadow, (toggle_rect.x, toggle_rect.y + 3))
    pygame.draw.rect(screen, color, toggle_rect, border_radius=8)
    pygame.draw.rect(screen, lighten_color(color, 40), toggle_rect, width=2, border_radius=8)
    toggle_text = "ON" if is_on else "OFF"
    toggle_surf = toggle_font.render(toggle_text, True, COLOR_WHITE)
    screen.blit(toggle_surf, toggle_surf.get_rect(center=toggle_rect.center))

    return toggle_rect


def run_settings(screen, clock, settings, high_score=0, save_callback=None):

    if "music_volume" not in settings:
        settings["music_volume"] = 0.5
    if "sfx_volume" not in settings:
        settings["sfx_volume"] = 0.7
    if "screen_shake" not in settings:
        settings["screen_shake"] = True
    if "particles" not in settings:
        settings["particles"] = True

    row_label_font = casino_font(26)
    row_toggle_font = casino_font(24)
    title_font = casino_font(60)
    label_font = casino_font(24, bold=False)
    back_font = casino_font(32)

    row_total_width = LABEL_WIDTH + ROW_GAP + TOGGLE_WIDTH
    column_x = screen.get_width() // 2 - row_total_width // 2
    title_y = screen.get_height() // 2 - 320

    music_row_y = title_y + 70
    music_slider_rect = pygame.Rect(column_x, music_row_y + ROW_HEIGHT + 44, row_total_width, 10)

    sfx_row_y = music_slider_rect.y + 60
    sfx_slider_rect = pygame.Rect(column_x, sfx_row_y + ROW_HEIGHT + 44, row_total_width, 10)

    shake_row_y = sfx_slider_rect.y + 60
    particles_row_y = shake_row_y + ROW_HEIGHT + 14

    back_btn_rect = pygame.Rect(column_x, particles_row_y + ROW_HEIGHT + 30, row_total_width, 56)

    music_slider_hitbox = music_slider_rect.inflate(20, 20)
    sfx_slider_hitbox = sfx_slider_rect.inflate(20, 20)

    gradient_bg = build_gradient_background(screen.get_width(), screen.get_height())

    try:
        click_sound = pygame.mixer.Sound(
            os.path.join(BASE_DIR, "asset", "sounds", "click.mp3")
        )
        click_sound.set_volume(settings["sfx_volume"])
    except Exception as error:
        print(f"[SOUND WARNING] Could not load click.mp3 in settings: {error}")
        click_sound = DummySound()

    dragging_music_slider = False
    dragging_sfx_slider = False

    running = True
    while running:
        screen.blit(gradient_bg, (0, 0))

        draw_text_shadow(screen, title_font, "Settings", COLOR_WHITE, (screen.get_width() // 2, title_y))

        mouse_pos = pygame.mouse.get_pos()

        if dragging_music_slider:
            settings["music_volume"] = get_volume_from_mouse(
                mouse_pos[0], music_slider_rect.x, music_slider_rect.width
            )
            pygame.mixer.music.set_volume(settings["music_volume"])

        if dragging_sfx_slider:
            settings["sfx_volume"] = get_volume_from_mouse(
                mouse_pos[0], sfx_slider_rect.x, sfx_slider_rect.width
            )
            click_sound.set_volume(settings["sfx_volume"])

        music_toggle_rect = draw_setting_row(
            screen, column_x, music_row_y, "Music", settings["music"], mouse_pos,
            row_label_font, row_toggle_font,
        )

        music_slider_label = label_font.render("Music Volume", True, COLOR_WHITE)
        screen.blit(music_slider_label, (column_x, music_slider_rect.y - 28))
        draw_volume_slider(
            screen,
            music_slider_rect,
            settings["music_volume"],
            is_active=music_slider_hitbox.collidepoint(mouse_pos)
            or dragging_music_slider,
        )

        sfx_toggle_rect = draw_setting_row(
            screen, column_x, sfx_row_y, "SFX", settings["sfx"], mouse_pos,
            row_label_font, row_toggle_font,
        )

        sfx_slider_label = label_font.render("SFX Volume", True, COLOR_WHITE)
        screen.blit(sfx_slider_label, (column_x, sfx_slider_rect.y - 28))
        draw_volume_slider(
            screen,
            sfx_slider_rect,
            settings["sfx_volume"],
            is_active=sfx_slider_hitbox.collidepoint(mouse_pos) or dragging_sfx_slider,
        )

        shake_toggle_rect = draw_setting_row(
            screen, column_x, shake_row_y, "Screen Shake", settings["screen_shake"], mouse_pos,
            row_label_font, row_toggle_font,
        )
        particles_toggle_rect = draw_setting_row(
            screen, column_x, particles_row_y, "Particles", settings["particles"], mouse_pos,
            row_label_font, row_toggle_font,
        )

        draw_button(screen, back_btn_rect, "Back", back_font, COLOR_PURPLE_DARK, mouse_pos, key="settings_back")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if save_callback:
                    save_callback(high_score, settings)
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if music_toggle_rect.collidepoint(event.pos):
                    if settings["sfx"]:
                        click_sound.play()
                    settings["music"] = not settings["music"]

                    if settings["music"]:
                        pygame.mixer.music.unpause()
                        pygame.mixer.music.set_volume(settings["music_volume"])
                        if not pygame.mixer.music.get_busy():
                            try:
                                pygame.mixer.music.play(-1)
                            except Exception as error:
                                print(
                                    f"[MUSIC WARNING] Could not resume background music: {error}"
                                )
                    else:
                        pygame.mixer.music.pause()

                elif music_slider_hitbox.collidepoint(event.pos):
                    dragging_music_slider = True
                    settings["music_volume"] = get_volume_from_mouse(
                        event.pos[0], music_slider_rect.x, music_slider_rect.width
                    )
                    pygame.mixer.music.set_volume(settings["music_volume"])

                elif sfx_toggle_rect.collidepoint(event.pos):
                    settings["sfx"] = not settings["sfx"]
                    if settings["sfx"]:
                        click_sound.play()

                elif sfx_slider_hitbox.collidepoint(event.pos):
                    dragging_sfx_slider = True
                    settings["sfx_volume"] = get_volume_from_mouse(
                        event.pos[0], sfx_slider_rect.x, sfx_slider_rect.width
                    )
                    click_sound.set_volume(settings["sfx_volume"])

                elif shake_toggle_rect.collidepoint(event.pos):
                    settings["screen_shake"] = not settings["screen_shake"]
                    if settings["sfx"]:
                        click_sound.play()

                elif particles_toggle_rect.collidepoint(event.pos):
                    settings["particles"] = not settings["particles"]
                    if settings["sfx"]:
                        click_sound.play()

                elif back_btn_rect.collidepoint(event.pos):
                    if settings["sfx"]:
                        click_sound.play()
                    register_click_flash("settings_back")
                    return settings

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging_music_slider = False
                dragging_sfx_slider = False

        pygame.display.flip()
        clock.tick(60)