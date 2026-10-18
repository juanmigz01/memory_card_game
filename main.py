import os
import sys
import json
import math
import pygame
from game import run_game, load_card_assets
from setting import run_settings
from effects import (
    FallingCardsBackground, casino_font,
    build_gradient_background, draw_button, draw_text_shadow, lighten_color,
    register_click_flash, draw_panel, draw_pill_button, draw_close_button,
)
from end import show_end_screen

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

if getattr(sys, "frozen", False):
    ASSET_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    SAVE_DIR = os.path.dirname(sys.executable)
else:
    ASSET_DIR = os.path.dirname(__file__)
    SAVE_DIR = os.path.dirname(__file__)

COLOR_BLACK = (12, 10, 16)
COLOR_WHITE = (240, 238, 245)
COLOR_PURPLE = (147, 51, 234)
COLOR_PURPLE_DARK = (88, 28, 135)
COLOR_PURPLE_LIGHT = (196, 156, 255)
COLOR_GOLD = (212, 175, 55)


class DummySound:

    def play(self):
        pass

    def set_volume(self, vol):
        pass


def load_sound(filename):
    path = os.path.join(ASSET_DIR, "asset", "sounds", filename)
    try:
        return pygame.mixer.Sound(path)
    except Exception as error:
        print(f"[SOUND WARNING] Could not load '{path}': {error}")
        return DummySound()


def play_sfx(sound, settings):
    if settings["sfx"]:
        sound.set_volume(settings["sfx_volume"])
        sound.play()


SAVE_FILE_PATH = os.path.join(SAVE_DIR, "save_data.json")


def load_save_data():
    default_data = {
        "high_score": 0,
        "settings": {
            "music": True,
            "sfx": True,
            "music_volume": 0.5,
            "sfx_volume": 0.7,
            "screen_shake": True,
            "particles": True,
        },
    }

    if not os.path.exists(SAVE_FILE_PATH):
        return default_data

    try:
        with open(SAVE_FILE_PATH, "r") as file:
            loaded_data = json.load(file)

        default_data["high_score"] = loaded_data.get("high_score", 0)
        default_data["settings"].update(loaded_data.get("settings", {}))
        return default_data

    except Exception as error:
        print(f"[SAVE WARNING] Could not read save file, using defaults: {error}")
        return default_data


def save_game_data(high_score, settings):
    data_to_save = {
        "high_score": high_score,
        "settings": settings,
    }
    try:
        with open(SAVE_FILE_PATH, "w") as file:
            json.dump(data_to_save, file, indent=4)
    except Exception as error:
        print(f"[SAVE WARNING] Could not write save file: {error}")


save_data = load_save_data()
high_score = save_data["high_score"]
settings = save_data["settings"]

try:
    music_path = os.path.join(ASSET_DIR, "asset", "sounds", "background.mp3")
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.set_volume(settings["music_volume"])
    pygame.mixer.music.play(-1)
except Exception as error:
    print(f"[MUSIC WARNING] Could not load background music: {error}")

click_sound = load_sound("click.mp3")
game_start_sound = load_sound("game_start.mp3")


display_info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Memory Card Matching Game")
clock = pygame.time.Clock()

title_font = casino_font(70)
panel_title_font = casino_font(30)
pill_button_font = casino_font(26)
hs_font = casino_font(32)

MENU_BTN_WIDTH, MENU_BTN_HEIGHT = 260, 56
menu_btn_x = SCREEN_WIDTH // 2 - MENU_BTN_WIDTH // 2
menu_btn_start_y = SCREEN_HEIGHT // 2 - 20

start_btn_rect = pygame.Rect(menu_btn_x, menu_btn_start_y, MENU_BTN_WIDTH, MENU_BTN_HEIGHT)
settings_btn_rect = pygame.Rect(menu_btn_x, menu_btn_start_y + (MENU_BTN_HEIGHT + 22), MENU_BTN_WIDTH, MENU_BTN_HEIGHT)
quit_btn_rect = pygame.Rect(menu_btn_x, menu_btn_start_y + 2 * (MENU_BTN_HEIGHT + 22), MENU_BTN_WIDTH, MENU_BTN_HEIGHT)

try:
    card_images = load_card_assets(
        "asset/images/card-sheet.png", "asset/images/card-sheet.json"
    )
    falling_card_source = card_images["Back"]
except Exception as error:
    print(f"[ASSET WARNING] Could not load card art for menu background: {error}")
    falling_card_source = pygame.Surface((100, 146))
    falling_card_source.fill(COLOR_PURPLE_DARK)

falling_bg = FallingCardsBackground(falling_card_source, SCREEN_WIDTH, SCREEN_HEIGHT, count=18)
menu_gradient_bg = build_gradient_background(SCREEN_WIDTH, SCREEN_HEIGHT)


def draw_main_menu():
    screen.blit(menu_gradient_bg, (0, 0))

    falling_bg.update()
    falling_bg.draw(screen)

    draw_text_shadow(screen, title_font, "Memory Card Game", COLOR_WHITE, (SCREEN_WIDTH // 2, menu_btn_start_y - 110))
    draw_text_shadow(
        screen, hs_font, f"High Score: {high_score}", COLOR_GOLD, (SCREEN_WIDTH // 2, menu_btn_start_y - 55)
    )

    mouse_pos = pygame.mouse.get_pos()

    draw_pill_button(screen, start_btn_rect, "START", pill_button_font, mouse_pos, key="menu_start")
    draw_pill_button(screen, settings_btn_rect, "SETTINGS", pill_button_font, mouse_pos, key="menu_settings")
    draw_pill_button(screen, quit_btn_rect, "QUIT", pill_button_font, mouse_pos, key="menu_quit")


DIFFICULTIES = [
    ("Easy", 15),
    ("Normal", 10),
    ("Hard", 5),
    ("Extreme", 1),
]


def select_difficulty():
    panel_font = casino_font(30)
    button_font = casino_font(24)

    panel_w, panel_h = 380, 500
    panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
    panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    btn_w, btn_h = 260, 56
    btn_x = panel_rect.centerx - btn_w // 2
    start_y = panel_rect.y + 90

    rects = []
    for index in range(len(DIFFICULTIES)):
        rects.append(pygame.Rect(btn_x, start_y + index * (btn_h + 18), btn_w, btn_h))

    close_center = (panel_rect.centerx, panel_rect.bottom - 34)

    choosing = True
    while choosing:
        screen.blit(menu_gradient_bg, (0, 0))
        falling_bg.update()
        falling_bg.draw(screen)

        mouse_pos = pygame.mouse.get_pos()

        draw_panel(screen, panel_rect, "DIFFICULTY", panel_font)

        for index, (name, hearts) in enumerate(DIFFICULTIES):
            draw_pill_button(screen, rects[index], name.upper(), button_font, mouse_pos, key=f"diff_{name}")

        draw_close_button(screen, close_center, 26, mouse_pos, key="diff_close")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data(high_score, settings)
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dist = math.hypot(event.pos[0] - close_center[0], event.pos[1] - close_center[1])
                if dist <= 30:
                    play_sfx(click_sound, settings)
                    register_click_flash("diff_close")
                    return None

                for index, (name, hearts) in enumerate(DIFFICULTIES):
                    if not rects[index].collidepoint(event.pos):
                        continue
                    play_sfx(click_sound, settings)
                    register_click_flash(f"diff_{name}")
                    return hearts

        pygame.display.flip()
        clock.tick(60)

        pygame.display.flip()
        clock.tick(60)


in_menu = True
while in_menu:

    if settings["music"]:
        if not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.play(-1)
            except Exception as error:
                print(f"[MUSIC WARNING] Could not resume background music: {error}")
    else:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game_data(high_score, settings)
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            save_game_data(high_score, settings)
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if start_btn_rect.collidepoint(event.pos):
                play_sfx(click_sound, settings)
                register_click_flash("menu_start")
                chosen_hearts = select_difficulty()
                if chosen_hearts is not None:
                    play_sfx(game_start_sound, settings)
                    final_score, high_score = run_game(
                        screen, clock, high_score, settings,
                        save_callback=save_game_data, starting_hearts=chosen_hearts,
                    )
                    save_game_data(high_score, settings)

            elif settings_btn_rect.collidepoint(event.pos):
                play_sfx(click_sound, settings)
                register_click_flash("menu_settings")
                settings = run_settings(
                    screen,
                    clock,
                    settings,
                    high_score=high_score,
                    save_callback=save_game_data,
                )
                pygame.mixer.music.set_volume(settings["music_volume"])
                save_game_data(high_score, settings)

            elif quit_btn_rect.collidepoint(event.pos):
                play_sfx(click_sound, settings)
                register_click_flash("menu_quit")
                save_game_data(high_score, settings)
                show_end_screen(screen, clock)
                pygame.quit()
                sys.exit()

    draw_main_menu()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()