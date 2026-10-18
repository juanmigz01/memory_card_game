import sys
import webbrowser
import pygame
from effects import (
    casino_font, build_gradient_background, draw_button, draw_text_shadow, register_click_flash,
)

COLOR_BLACK = (12, 10, 16)
COLOR_WHITE = (240, 238, 245)
COLOR_PURPLE = (147, 51, 234)
COLOR_PURPLE_DARK = (88, 28, 135)
COLOR_PURPLE_LIGHT = (196, 156, 255)
COLOR_GOLD = (212, 175, 55)

ITCH_URL = "https://katsumi001.itch.io/"
GITHUB_URL = "https://github.com/juanmigz01"


def show_end_screen(screen, clock):
    screen_w, screen_h = screen.get_size()

    title_font = casino_font(70)
    sub_font = casino_font(30)
    link_font = casino_font(34)
    exit_font = casino_font(30)

    title_y = screen_h // 2 - 180
    sub_y = title_y + 80

    itch_btn_rect = pygame.Rect(screen_w // 2 - 170, sub_y + 90, 340, 58)
    github_btn_rect = pygame.Rect(screen_w // 2 - 170, itch_btn_rect.bottom + 20, 340, 58)
    exit_btn_rect = pygame.Rect(screen_w // 2 - 110, github_btn_rect.bottom + 50, 220, 54)

    gradient_bg = build_gradient_background(screen_w, screen_h)

    waiting = True
    while waiting:
        screen.blit(gradient_bg, (0, 0))

        draw_text_shadow(screen, title_font, "Thanks for playing!", COLOR_WHITE, (screen_w // 2, title_y))
        draw_text_shadow(screen, sub_font, "Check out more of my work:", COLOR_GOLD, (screen_w // 2, sub_y))

        mouse_pos = pygame.mouse.get_pos()

        draw_button(screen, itch_btn_rect, "itch.io Profile", link_font, COLOR_PURPLE, mouse_pos, key="end_itch")
        draw_button(screen, github_btn_rect, "GitHub Profile", link_font, COLOR_PURPLE_DARK, mouse_pos, key="end_github")
        draw_button(screen, exit_btn_rect, "Exit", exit_font, (45, 45, 60), mouse_pos, key="end_exit")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if itch_btn_rect.collidepoint(event.pos):
                    register_click_flash("end_itch")
                    try:
                        webbrowser.open(ITCH_URL)
                    except Exception as error:
                        print(f"[LINK WARNING] Could not open itch.io link: {error}")

                elif github_btn_rect.collidepoint(event.pos):
                    register_click_flash("end_github")
                    try:
                        webbrowser.open(GITHUB_URL)
                    except Exception as error:
                        print(f"[LINK WARNING] Could not open GitHub link: {error}")

                elif exit_btn_rect.collidepoint(event.pos):
                    register_click_flash("end_exit")
                    return

        pygame.display.flip()
        clock.tick(60)