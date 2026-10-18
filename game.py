import json
import os
import random
import sys
import math
import pygame
from card import Card
from effects import (
    ScreenShake, ParticleSystem, casino_font,
    build_gradient_background, draw_button, draw_text_shadow, lighten_color,
    draw_heart_icon, register_click_flash,
    draw_panel, draw_pill_button, draw_close_button, draw_star,
)
from end import show_end_screen

CARD_NAMES = [
    "A",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
    "Joker",
    "Back",
]

BASE_DIR = os.path.dirname(__file__)

STARTING_CARD_COUNT = 4
MAX_CARD_COUNT = 20
CARDS_ADDED_PER_LEVEL = 4

STARTING_HEARTS = 15
MAX_HEARTS = 20

POINTS_PER_MATCH = 2
MATCHES_IN_A_ROW_FOR_BONUS_HEART = 2

COUNTDOWN_DURATION_MS = 3000
PREVIEW_DURATION_MS = 1000
FLIP_BACK_DELAY_MS = 1000
GAME_OVER_DURATION_MS = 3000
WIN_FLASH_DURATION_MS = 450
DEAL_STAGGER_MS = 100

HELP_MIN_STARTING_HEARTS = 10
HELP_UNLOCK_HEARTS = 1
HINT_DURATION_MS = 1500
COLOR_HINT_GREEN = (60, 220, 110)

COLOR_BLACK = (12, 10, 16)
COLOR_WHITE = (240, 238, 245)
COLOR_PURPLE = (147, 51, 234)
COLOR_PURPLE_DARK = (88, 28, 135)
COLOR_PURPLE_LIGHT = (196, 156, 255)
COLOR_WOOD = (92, 51, 23)
COLOR_WOOD_DARK = (58, 30, 13)
COLOR_WOOD_TRIM = (128, 78, 40)
COLOR_FELT = (18, 66, 38)
COLOR_FELT_LIGHT = (26, 84, 48)
COLOR_GOLD = (212, 175, 55)
COLOR_HEART_RED = (196, 30, 45)
COLOR_WIN_TINT = (30, 190, 105)
COLOR_LOSE_TINT = (210, 45, 60)

PARTICLE_COLORS = [(212, 175, 55), (196, 156, 255), (147, 51, 234), (240, 238, 245)]


class DummySound:

    def play(self):
        pass

    def set_volume(self, vol):
        pass

    def stop(self):
        pass


def load_sound(filename):
    path = os.path.join(BASE_DIR, "asset", "sounds", filename)
    try:
        return pygame.mixer.Sound(path)
    except Exception as error:
        print(f"[SOUND WARNING] Could not load '{path}': {error}")
        return DummySound()


def play_sfx(sound, settings, volume_scale=1.0):
    if settings["sfx"]:
        sound.set_volume(settings["sfx_volume"] * volume_scale)
        sound.play()


def load_card_assets(png_path, json_path):
    sheet = pygame.image.load(os.path.join(BASE_DIR, png_path)).convert_alpha()

    with open(os.path.join(BASE_DIR, json_path), "r") as file:
        data = json.load(file)

    card_dictionary = {}
    frames = data["frames"]

    for idx, (frame_key, frame_info) in enumerate(frames.items()):
        if idx >= len(CARD_NAMES):
            break

        rect_data = frame_info["frame"]
        x, y, w, h = rect_data["x"], rect_data["y"], rect_data["w"], rect_data["h"]

        card_surface = sheet.subsurface(pygame.Rect(x, y, w, h))
        card_name = CARD_NAMES[idx]
        card_dictionary[card_name] = card_surface

    return card_dictionary


def get_grid_columns(num_cards):
    if num_cards == STARTING_CARD_COUNT:
        return 2
    elif num_cards == MAX_CARD_COUNT:
        return 5
    else:
        return 4


def create_level_board(num_cards, card_dict, screen_w, screen_h):
    cards_list = []

    available_faces = [name for name in CARD_NAMES if name not in ["Joker", "Back"]]

    num_pairs = num_cards // 2
    selected_faces = random.sample(available_faces, num_pairs)

    board_faces = selected_faces * 2
    random.shuffle(board_faces)

    cols = get_grid_columns(num_cards)
    rows = num_cards // cols

    card_w, card_h = 100, 146
    padding = 28

    grid_w = cols * card_w + (cols - 1) * padding
    grid_h = rows * card_h + (rows - 1) * padding
    start_x = (screen_w - grid_w) // 2
    start_y = (screen_h - grid_h) // 2 + 30

    for i, face in enumerate(board_faces):
        col_idx = i % cols
        row_idx = i // cols

        x = start_x + col_idx * (card_w + padding)
        y = start_y + row_idx * (card_h + padding)

        new_card = Card(
            val=face,
            front_img=card_dict[face],
            back_img=card_dict["Back"],
            x=x,
            y=y,
        )
        cards_list.append(new_card)

    return cards_list


def draw_result_overlay(surface, screen_w, screen_h, tint_color, alpha=100):
    overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
    overlay.fill((*tint_color, alpha))
    surface.blit(overlay, (0, 0))


def draw_pop_text(surface, font, text, color, center, entry_elapsed_ms, pop_duration_ms=320):
    progress = min(1.0, max(0.0, entry_elapsed_ms) / pop_duration_ms)
    eased = 1 - (1 - progress) ** 3
    scale = 1.5 - 0.5 * eased

    base_surf = font.render(text, True, color)
    scaled_w = max(1, int(base_surf.get_width() * scale))
    scaled_h = max(1, int(base_surf.get_height() * scale))
    scaled_surf = pygame.transform.smoothscale(base_surf, (scaled_w, scaled_h))
    rect = scaled_surf.get_rect(center=center)
    surface.blit(scaled_surf, rect)


def draw_stat_box(surface, x, y, text, base_color, font, height=42):
    text_surf = font.render(text, True, COLOR_WHITE)
    box_width = text_surf.get_width() + 28
    rect = pygame.Rect(x, y, box_width, height)

    shadow_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 90), shadow_surf.get_rect(), border_radius=10)
    surface.blit(shadow_surf, (rect.x, rect.y + 3))

    pygame.draw.rect(surface, base_color, rect, border_radius=10)
    pygame.draw.rect(surface, lighten_color(base_color, 35), rect, width=2, border_radius=10)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))

    return rect.width


def draw_heart_stat_box(surface, x, y, value_text, base_color, font, height=42):
    text_surf = font.render(value_text, True, COLOR_WHITE)
    icon_gap = 10
    icon_width = 28
    box_width = icon_width + icon_gap + text_surf.get_width() + 28
    rect = pygame.Rect(x, y, box_width, height)

    shadow_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 90), shadow_surf.get_rect(), border_radius=10)
    surface.blit(shadow_surf, (rect.x, rect.y + 3))

    pygame.draw.rect(surface, base_color, rect, border_radius=10)
    pygame.draw.rect(surface, lighten_color(base_color, 35), rect, width=2, border_radius=10)

    icon_center = (rect.x + 20, rect.centery)
    draw_heart_icon(surface, icon_center, COLOR_WHITE, pixel_size=3)

    text_x = rect.x + 20 + icon_width // 2 + icon_gap
    text_rect = text_surf.get_rect(midleft=(text_x, rect.centery))
    surface.blit(text_surf, text_rect)

    return rect.width


def draw_table(surface, screen_w, screen_h):
    table_rect = pygame.Rect(20, 62, screen_w - 40, screen_h - 90)
    pygame.draw.rect(surface, COLOR_WOOD_DARK, table_rect, border_radius=28)

    trim_rect = table_rect.inflate(-26, -26)
    pygame.draw.rect(surface, COLOR_WOOD, trim_rect, border_radius=22)
    pygame.draw.rect(surface, COLOR_WOOD_TRIM, trim_rect, width=4, border_radius=22)

    inner_rect = trim_rect.inflate(-44, -44)
    pygame.draw.rect(surface, COLOR_FELT, inner_rect, border_radius=16)
    pygame.draw.rect(surface, COLOR_FELT_LIGHT, inner_rect, width=3, border_radius=16)


def run_game(screen, clock, high_score, settings, save_callback=None, starting_hearts=STARTING_HEARTS):

    card_images = load_card_assets(
        "asset/images/card-sheet.png", "asset/images/card-sheet.json"
    )

    card_flip_sound = load_sound("card_flip.mp3")
    click_sound = load_sound("click.mp3")
    countdown_sound = load_sound("countdown.mp3")
    match_success_sound = load_sound("match_success.mp3")
    match_lose_sound = load_sound("match_lose.mp3")
    gain_heart_sound = load_sound("gain_heart.mp3")
    game_over_sound = load_sound("game_over.mp3")
    reach_highscore_sound = load_sound("reach_highscore.mp3")

    screen_w, screen_h = screen.get_size()
    draw_surface = pygame.Surface((screen_w, screen_h))
    gradient_bg = build_gradient_background(screen_w, screen_h)

    settings.setdefault("screen_shake", True)
    settings.setdefault("particles", True)

    screen_shake = ScreenShake()
    particles = ParticleSystem()
    score = 0
    hearts = starting_hearts
    current_level = 1
    cards_count = STARTING_CARD_COUNT
    multiplier = 1
    consecutive_matches = 0
    high_score_broken = False

    ui_font = casino_font(32)
    countdown_font = casino_font(170)
    button_font = casino_font(28)
    panel_title_font = casino_font(30)
    panel_button_font = casino_font(24)
    small_panel_button_font = casino_font(18)
    clear_word_font = casino_font(90)
    gameover_word_font = casino_font(58)

    pause_btn_font = casino_font(22)
    pause_btn_rect = pygame.Rect(screen_w - 130, 15, 110, 42)
    help_btn_rect = pygame.Rect(20, screen_h // 2 - 30, 110, 60)

    result_panel_rect = pygame.Rect(0, 0, 380, 420)
    result_panel_rect.center = (screen_w // 2, screen_h // 2)
    result_btn_w, result_btn_h = 260, 54
    result_btn_x = result_panel_rect.centerx - result_btn_w // 2

    win_panel_rect = pygame.Rect(0, 0, 580, 260)
    win_panel_rect.center = (screen_w // 2, screen_h // 2)

    win_btn_w, win_btn_h = 150, 46
    win_btn_gap = 20
    win_row_width = win_btn_w * 2 + win_btn_gap
    win_row_x = win_panel_rect.centerx - win_row_width // 2
    win_row_y = win_panel_rect.y + 175
    next_btn_rect = pygame.Rect(win_row_x, win_row_y, win_btn_w, win_btn_h)
    win_exit_btn_rect = pygame.Rect(win_row_x + win_btn_w + win_btn_gap, win_row_y, win_btn_w, win_btn_h)

    lose_panel_rect = pygame.Rect(0, 0, 580, 260)
    lose_panel_rect.center = (screen_w // 2, screen_h // 2)
    lose_retry_btn_rect = pygame.Rect(win_row_x, win_row_y, win_btn_w, win_btn_h)
    lose_menu_btn_rect = pygame.Rect(win_row_x + win_btn_w + win_btn_gap, win_row_y, win_btn_w, win_btn_h)

    pause_panel_rect = pygame.Rect(0, 0, 380, 460)
    pause_panel_rect.center = (screen_w // 2, screen_h // 2)
    pause_btn_w, pause_btn_h = 260, 54
    pause_btn_x = pause_panel_rect.centerx - pause_btn_w // 2
    pause_start_y = pause_panel_rect.y + 95
    pause_new_game_rect = pygame.Rect(pause_btn_x, pause_start_y, pause_btn_w, pause_btn_h)
    pause_continue_rect = pygame.Rect(pause_btn_x, pause_start_y + (pause_btn_h + 16), pause_btn_w, pause_btn_h)
    pause_settings_rect = pygame.Rect(pause_btn_x, pause_start_y + 2 * (pause_btn_h + 16), pause_btn_w, pause_btn_h)
    pause_exit_rect = pygame.Rect(pause_btn_x, pause_start_y + 3 * (pause_btn_h + 16), pause_btn_w, pause_btn_h)
    pause_close_center = (pause_panel_rect.centerx, pause_panel_rect.bottom - 34)

    pause_toggle_w, pause_toggle_h = 260, 48
    pause_toggle_start_y = pause_panel_rect.y + 95
    pause_music_rect = pygame.Rect(pause_btn_x, pause_toggle_start_y, pause_toggle_w, pause_toggle_h)
    pause_sfx_rect = pygame.Rect(pause_btn_x, pause_toggle_start_y + (pause_toggle_h + 14), pause_toggle_w, pause_toggle_h)
    pause_shake_rect = pygame.Rect(pause_btn_x, pause_toggle_start_y + 2 * (pause_toggle_h + 14), pause_toggle_w, pause_toggle_h)
    pause_particles_rect = pygame.Rect(pause_btn_x, pause_toggle_start_y + 3 * (pause_toggle_h + 14), pause_toggle_w, pause_toggle_h)
    pause_settings_back_rect = pygame.Rect(pause_btn_x, pause_toggle_start_y + 4 * (pause_toggle_h + 14) + 8, pause_toggle_w, pause_toggle_h)

    STATE_COUNTDOWN = "COUNTDOWN"
    STATE_PREVIEW = "PREVIEW"
    STATE_PLAYING = "PLAYING"
    STATE_WIN_FLASH = "WIN_FLASH"
    STATE_WIN_READY = "WIN_READY"
    STATE_GAMEOVER = "GAMEOVER"
    STATE_PAUSED = "PAUSED"

    active_cards = []
    selected_cards = []
    flip_timer = None
    game_state = STATE_COUNTDOWN
    state_timer = pygame.time.get_ticks()
    preview_flipped = False
    hint_cards = []
    hint_timer = 0
    help_used = False
    state_before_pause = STATE_PLAYING
    pause_view = "menu"

    def start_new_level(is_first_level=False):
        nonlocal active_cards, game_state, state_timer, selected_cards, flip_timer
        nonlocal consecutive_matches, preview_flipped, hint_cards, help_used

        active_cards = create_level_board(cards_count, card_images, screen_w, screen_h)
        selected_cards = []
        flip_timer = None
        consecutive_matches = 0
        preview_flipped = False
        hint_cards = []
        help_used = False

        deck_point = (screen_w // 2 - 50, 96)
        for index, card in enumerate(active_cards):
            card.start_deal(deck_point, delay_ms=index * DEAL_STAGGER_MS)

        if is_first_level:
            game_state = STATE_COUNTDOWN
            play_sfx(countdown_sound, settings)
        else:
            game_state = STATE_PREVIEW

        state_timer = pygame.time.get_ticks()

    def reset_run():
        nonlocal score, hearts, current_level, cards_count, multiplier
        score = 0
        hearts = starting_hearts
        current_level = 1
        cards_count = STARTING_CARD_COUNT
        multiplier = 1
        start_new_level(is_first_level=True)

    start_new_level(is_first_level=True)

    playing_game = True
    while playing_game:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()

        if settings["music"]:
            pygame.mixer.music.set_volume(settings["music_volume"])
            if not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.play(-1)
                except Exception as error:
                    print(f"[MUSIC WARNING] Could not resume background music: {error}")
        else:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()

        if score > high_score:
            if not high_score_broken and high_score > 0:
                play_sfx(reach_highscore_sound, settings)
                high_score_broken = True
            high_score = score

        screen_shake.update(dt)
        particles.update(dt)

        if hint_cards and current_time - hint_timer >= HINT_DURATION_MS:
            hint_cards = []

        if game_state != STATE_PAUSED:
            for card in active_cards:
                card.update(dt)

        if game_state == STATE_COUNTDOWN:
            if current_time - state_timer >= COUNTDOWN_DURATION_MS:
                countdown_sound.stop()
                game_state = STATE_PREVIEW
                preview_flipped = False
                state_timer = current_time

        elif game_state == STATE_PREVIEW:
            if not preview_flipped:
                if not any(card.is_dealing for card in active_cards):
                    for card in active_cards:
                        card.is_flipped = True
                    preview_flipped = True
                    state_timer = current_time
            else:
                if current_time - state_timer >= PREVIEW_DURATION_MS:
                    for card in active_cards:
                        card.is_flipped = False
                    game_state = STATE_PLAYING

        elif game_state == STATE_WIN_FLASH:
            if current_time - state_timer >= WIN_FLASH_DURATION_MS:
                game_state = STATE_WIN_READY
                state_timer = current_time

        elif game_state == STATE_PLAYING:
            if flip_timer and current_time - flip_timer >= FLIP_BACK_DELAY_MS:
                for card in selected_cards:
                    card.flip()
                selected_cards.clear()
                flip_timer = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if save_callback:
                    save_callback(high_score, settings)
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                if game_state == STATE_PAUSED:
                    if pause_view == "menu":
                        dist = math.hypot(mouse_pos[0] - pause_close_center[0], mouse_pos[1] - pause_close_center[1])
                        if dist <= 30:
                            play_sfx(click_sound, settings)
                            register_click_flash("pause_close")
                            game_state = state_before_pause
                        elif pause_new_game_rect.collidepoint(mouse_pos):
                            play_sfx(click_sound, settings)
                            register_click_flash("pause_new_game")
                            reset_run()
                        elif pause_continue_rect.collidepoint(mouse_pos):
                            play_sfx(click_sound, settings)
                            register_click_flash("pause_continue")
                            game_state = state_before_pause
                        elif pause_settings_rect.collidepoint(mouse_pos):
                            play_sfx(click_sound, settings)
                            register_click_flash("pause_settings")
                            pause_view = "settings"
                        elif pause_exit_rect.collidepoint(mouse_pos):
                            play_sfx(click_sound, settings)
                            register_click_flash("pause_exit")
                            countdown_sound.stop()
                            return score, high_score
                    else:
                        dist = math.hypot(mouse_pos[0] - pause_close_center[0], mouse_pos[1] - pause_close_center[1])
                        if dist <= 30:
                            register_click_flash("pause_settings_close")
                            pause_view = "menu"
                        elif pause_music_rect.collidepoint(mouse_pos):
                            settings["music"] = not settings["music"]
                            if settings["music"]:
                                pygame.mixer.music.unpause()
                            else:
                                pygame.mixer.music.pause()
                            register_click_flash("pause_music")
                        elif pause_sfx_rect.collidepoint(mouse_pos):
                            settings["sfx"] = not settings["sfx"]
                            if settings["sfx"]:
                                click_sound.play()
                            register_click_flash("pause_sfx")
                        elif pause_shake_rect.collidepoint(mouse_pos):
                            settings["screen_shake"] = not settings["screen_shake"]
                            register_click_flash("pause_shake")
                        elif pause_particles_rect.collidepoint(mouse_pos):
                            settings["particles"] = not settings["particles"]
                            register_click_flash("pause_particles")
                        elif pause_settings_back_rect.collidepoint(mouse_pos):
                            register_click_flash("pause_back")
                            pause_view = "menu"

                elif pause_btn_rect.collidepoint(mouse_pos) and game_state in (
                    STATE_PLAYING, STATE_PREVIEW, STATE_COUNTDOWN,
                ):
                    play_sfx(click_sound, settings)
                    register_click_flash("game_pause")
                    state_before_pause = game_state
                    pause_view = "menu"
                    game_state = STATE_PAUSED

                elif game_state == STATE_WIN_READY and next_btn_rect.collidepoint(mouse_pos):
                    play_sfx(click_sound, settings)
                    register_click_flash("game_next")
                    current_level += 1
                    if cards_count < MAX_CARD_COUNT:
                        cards_count += CARDS_ADDED_PER_LEVEL
                    start_new_level(is_first_level=False)

                elif game_state == STATE_WIN_READY and win_exit_btn_rect.collidepoint(mouse_pos):
                    play_sfx(click_sound, settings)
                    register_click_flash("game_win_exit")
                    countdown_sound.stop()
                    return score, high_score

                elif game_state == STATE_GAMEOVER and lose_retry_btn_rect.collidepoint(mouse_pos):
                    play_sfx(click_sound, settings)
                    register_click_flash("game_lose_retry")
                    reset_run()

                elif game_state == STATE_GAMEOVER and lose_menu_btn_rect.collidepoint(mouse_pos):
                    play_sfx(click_sound, settings)
                    register_click_flash("game_lose_menu")
                    countdown_sound.stop()
                    return score, high_score

                else:
                    help_available = (
                        not help_used
                        and starting_hearts >= HELP_MIN_STARTING_HEARTS
                        and hearts <= HELP_UNLOCK_HEARTS
                    )
                    if help_available and game_state == STATE_PLAYING and help_btn_rect.collidepoint(mouse_pos):
                        play_sfx(click_sound, settings)
                        register_click_flash("game_help")
                        remaining_by_val = {}
                        for card in active_cards:
                            if not card.is_matched and not card.is_removing and not card.is_removed:
                                remaining_by_val.setdefault(card.val, []).append(card)

                        hintable_pairs = [pair for pair in remaining_by_val.values() if len(pair) == 2]
                        if hintable_pairs:
                            hint_cards = random.choice(hintable_pairs)
                            hint_timer = current_time
                            help_used = True

                    elif game_state == STATE_PLAYING:
                        if len(selected_cards) < 2 and flip_timer is None:
                            for card in active_cards:
                                if not card.is_clicked(mouse_pos):
                                    continue

                                card.flip()
                                play_sfx(card_flip_sound, settings)
                                selected_cards.append(card)

                                if len(selected_cards) == 2:
                                    c1, c2 = selected_cards[0], selected_cards[1]

                                    if c1.val == c2.val:
                                        c1.is_matched = True
                                        c2.is_matched = True
                                        c1.start_remove()
                                        c2.start_remove()
                                        score += POINTS_PER_MATCH * multiplier
                                        play_sfx(match_success_sound, settings)

                                        if settings["particles"]:
                                            mid_x = (c1.rect.centerx + c2.rect.centerx) // 2
                                            mid_y = (c1.rect.centery + c2.rect.centery) // 2
                                            particles.burst(mid_x, mid_y, PARTICLE_COLORS)

                                        selected_cards.clear()

                                        consecutive_matches += 1
                                        if consecutive_matches == MATCHES_IN_A_ROW_FOR_BONUS_HEART:
                                            if hearts < MAX_HEARTS:
                                                hearts += 1
                                                play_sfx(gain_heart_sound, settings)
                                            consecutive_matches = 0

                                        if all(card.is_matched for card in active_cards):
                                            if hearts == MAX_HEARTS:
                                                multiplier = 2
                                            elif hearts < MAX_HEARTS:
                                                hearts += 1
                                                play_sfx(gain_heart_sound, settings)

                                            game_state = STATE_WIN_FLASH
                                            state_timer = current_time

                                    else:
                                        hearts -= 1
                                        flip_timer = current_time
                                        consecutive_matches = 0
                                        play_sfx(match_lose_sound, settings)

                                        if settings["screen_shake"]:
                                            screen_shake.add_trauma(0.55)

                                        if hearts <= 0:
                                            game_state = STATE_GAMEOVER
                                            play_sfx(game_over_sound, settings)
                                            state_timer = current_time
                                            if settings["screen_shake"]:
                                                screen_shake.add_trauma(1.0)

                                break
                        elif flip_timer is not None:
                            for card in selected_cards:
                                card.start_shake()
                            play_sfx(match_lose_sound, settings, volume_scale=0.4)
                            if settings["screen_shake"]:
                                screen_shake.add_trauma(0.35)

        def draw_hud():
            bar_rect = pygame.Rect(10, 10, screen_w - 20, 56)
            bar_surf = pygame.Surface(bar_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(bar_surf, (20, 15, 28, 160), bar_surf.get_rect(), border_radius=14)
            draw_surface.blit(bar_surf, bar_rect.topleft)

            hud_x = 22
            hud_gap = 22

            heart_box_width = draw_heart_stat_box(
                draw_surface, hud_x, 18, str(hearts), COLOR_HEART_RED, ui_font
            )
            hud_x += heart_box_width + hud_gap

            other_items = [
                (f"Lvl: {current_level}", COLOR_PURPLE_DARK),
                (f"Score: {score} ({multiplier}x)", (110, 88, 20)),
                (f"High: {high_score}", COLOR_PURPLE),
            ]
            for text, color in other_items:
                box_width = draw_stat_box(draw_surface, hud_x, 18, text, color, ui_font)
                hud_x += box_width + hud_gap

            mouse_pos = pygame.mouse.get_pos()
            draw_button(
                draw_surface, pause_btn_rect, "Pause", pause_btn_font, (60, 45, 90), mouse_pos, key="game_pause"
            )

        if game_state == STATE_COUNTDOWN:
            draw_surface.blit(gradient_bg, (0, 0))
            draw_table(draw_surface, screen_w, screen_h)

            mouse_pos = pygame.mouse.get_pos()
            for card in active_cards:
                card.draw(draw_surface, mouse_pos)

            seconds_elapsed = (current_time - state_timer) // 1000
            seconds_remaining = (COUNTDOWN_DURATION_MS // 1000) - seconds_elapsed
            display_text = str(seconds_remaining) if seconds_remaining > 0 else "GO!"

            local_progress = ((current_time - state_timer) % 1000) / 1000
            punch = 1.0 + 0.5 * max(0.0, 1.0 - local_progress * 4)

            base_surf = countdown_font.render(display_text, True, COLOR_GOLD)
            scaled_w = max(1, int(base_surf.get_width() * punch))
            scaled_h = max(1, int(base_surf.get_height() * punch))
            count_surf = pygame.transform.smoothscale(base_surf, (scaled_w, scaled_h))
            count_rect = count_surf.get_rect(center=(screen_w // 2, screen_h // 2))
            draw_surface.blit(count_surf, count_rect)

            draw_hud()

        elif game_state == STATE_GAMEOVER:
            draw_surface.blit(gradient_bg, (0, 0))
            draw_table(draw_surface, screen_w, screen_h)
            draw_result_overlay(draw_surface, screen_w, screen_h, COLOR_LOSE_TINT, alpha=90)

            mouse_pos = pygame.mouse.get_pos()
            draw_panel(draw_surface, lose_panel_rect, "", panel_title_font, show_header=False)

            gameover_word_surf = gameover_word_font.render("GAME OVER", True, COLOR_WHITE)
            gameover_word_rect = gameover_word_surf.get_rect(
                center=(lose_panel_rect.centerx, lose_panel_rect.y + 75)
            )
            draw_surface.blit(gameover_word_surf, gameover_word_rect)

            draw_text_shadow(
                draw_surface, small_panel_button_font, f"Final Score: {score}", COLOR_WHITE,
                (lose_panel_rect.centerx, lose_panel_rect.y + 135),
            )

            draw_pill_button(draw_surface, lose_retry_btn_rect, "RETRY", small_panel_button_font, mouse_pos, key="game_lose_retry")
            draw_pill_button(draw_surface, lose_menu_btn_rect, "MAIN MENU", small_panel_button_font, mouse_pos, key="game_lose_menu")

        elif game_state == STATE_WIN_READY:
            draw_surface.blit(gradient_bg, (0, 0))
            draw_table(draw_surface, screen_w, screen_h)
            draw_result_overlay(draw_surface, screen_w, screen_h, COLOR_WIN_TINT, alpha=90)

            mouse_pos = pygame.mouse.get_pos()
            draw_panel(draw_surface, win_panel_rect, "", panel_title_font, show_header=False)

            clear_word_surf = clear_word_font.render("CLEAR", True, COLOR_WHITE)
            clear_word_rect = clear_word_surf.get_rect(
                center=(win_panel_rect.centerx, win_panel_rect.y + 95)
            )
            draw_surface.blit(clear_word_surf, clear_word_rect)

            draw_pill_button(draw_surface, next_btn_rect, "NEXT", small_panel_button_font, mouse_pos, key="game_next")
            draw_pill_button(draw_surface, win_exit_btn_rect, "EXIT", small_panel_button_font, mouse_pos, key="game_win_exit")

            draw_hud()

        elif game_state == STATE_PAUSED:
            draw_surface.blit(gradient_bg, (0, 0))
            draw_table(draw_surface, screen_w, screen_h)

            for card in active_cards:
                card.draw(draw_surface)

            dim_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            dim_surf.fill((0, 0, 0, 140))
            draw_surface.blit(dim_surf, (0, 0))

            mouse_pos = pygame.mouse.get_pos()

            if pause_view == "menu":
                draw_panel(draw_surface, pause_panel_rect, "PAUSED", panel_title_font)
                draw_pill_button(draw_surface, pause_new_game_rect, "NEW GAME", panel_button_font, mouse_pos, key="pause_new_game")
                draw_pill_button(draw_surface, pause_continue_rect, "CONTINUE", panel_button_font, mouse_pos, key="pause_continue")
                draw_pill_button(draw_surface, pause_settings_rect, "SETTINGS", panel_button_font, mouse_pos, key="pause_settings")
                draw_pill_button(draw_surface, pause_exit_rect, "EXIT", panel_button_font, mouse_pos, key="pause_exit")
                draw_close_button(draw_surface, pause_close_center, 26, mouse_pos, key="pause_close")
            else:
                draw_panel(draw_surface, pause_panel_rect, "SETTINGS", panel_title_font)

                toggle_rows = [
                    ("Music", settings["music"], pause_music_rect, "pause_music"),
                    ("SFX", settings["sfx"], pause_sfx_rect, "pause_sfx"),
                    ("Screen Shake", settings["screen_shake"], pause_shake_rect, "pause_shake"),
                    ("Particles", settings["particles"], pause_particles_rect, "pause_particles"),
                ]
                for label, is_on, rect, key in toggle_rows:
                    text = f"{label}: {'ON' if is_on else 'OFF'}"
                    draw_pill_button(draw_surface, rect, text, panel_button_font, mouse_pos, key=key)

                draw_pill_button(draw_surface, pause_settings_back_rect, "BACK", panel_button_font, mouse_pos, key="pause_back")
                draw_close_button(draw_surface, pause_close_center, 26, mouse_pos, key="pause_settings_close")

        else:
            draw_surface.blit(gradient_bg, (0, 0))
            draw_table(draw_surface, screen_w, screen_h)

            mouse_pos = pygame.mouse.get_pos()
            for card in active_cards:
                card.draw(draw_surface, mouse_pos)

            if hint_cards:
                for card in hint_cards:
                    outline_rect = card.rect.inflate(8, 8)
                    pygame.draw.rect(draw_surface, COLOR_HINT_GREEN, outline_rect, width=4, border_radius=8)

            particles.draw(draw_surface)

            if game_state == STATE_WIN_FLASH:
                flash_progress = (current_time - state_timer) / WIN_FLASH_DURATION_MS
                flash_alpha = int(160 * max(0.0, 1.0 - flash_progress))
                flash_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
                flash_surf.fill((60, 220, 120, flash_alpha))
                draw_surface.blit(flash_surf, (0, 0))

            help_available = (
                not help_used
                and starting_hearts >= HELP_MIN_STARTING_HEARTS
                and hearts <= HELP_UNLOCK_HEARTS
            )
            if help_available and game_state == STATE_PLAYING:
                draw_button(
                    draw_surface, help_btn_rect, "Help", button_font, (40, 130, 80), mouse_pos,
                    key="game_help",
                )

            draw_hud()

        shake_x, shake_y = screen_shake.get_offset() if settings["screen_shake"] else (0, 0)
        screen.fill(COLOR_BLACK)
        screen.blit(draw_surface, (shake_x, shake_y))
        pygame.display.flip()

    return score, high_score