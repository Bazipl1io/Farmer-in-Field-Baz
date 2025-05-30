# -*- coding: utf-8 -*-
import pygame
import sys
import time
import os

# Пути к иконкам
ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
MONEY_ICON = os.path.join(ICONS_DIR, "money.png")
HARVEST_ICON = os.path.join(ICONS_DIR, "harvest.png")

# Настройки
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
SQUARE_SIZE = 30
GAP = 30
BG_COLOR = (34, 139, 34)
SQUARE_COLOR = (222, 184, 135)
CARROT_COLOR = (255, 140, 0)
CARROT_READY_COLOR = (200, 100, 0)
CABBAGE_COLOR = (120, 200, 80)
CABBAGE_READY_COLOR = (60, 120, 40)
FONT_COLOR = (0, 0, 0)
MENU_WIDTH = 300
MENU_BG = (255, 255, 255, 180)  # Прозрачный белый
TOPBAR_HEIGHT = 40
TOPBAR_BG = (230, 230, 230)
COORDS_COLOR = (255, 255, 255)
COORDS_BG = (0, 0, 0, 180)

# Культура: морковь
class Carrot:
    name = "Морковь"
    plant_color = CARROT_COLOR
    ready_color = CARROT_READY_COLOR
    grow_time = 10  # секунд
    yield_count = 4

    @staticmethod
    def get_color(state):
        return Carrot.ready_color if state == "ready" else Carrot.plant_color

# Культура: капуста
class Cabbage:
    name = "Капуста"
    plant_color = CABBAGE_COLOR
    ready_color = CABBAGE_READY_COLOR
    grow_time = 15  # секунд
    yield_count = 2

    @staticmethod
    def get_color(state):
        return Cabbage.ready_color if state == "ready" else Cabbage.plant_color

# Добавьте сюда новые культуры по аналогии

CROPS = [Carrot, Cabbage]
selected_crop_idx = 0

# Сетка: {(col, row): {"crop": CropClass, "plant_time": float, "state": "planted"/"ready"}}
field = {}

def get_square_by_pos(mx, my, offset_x, offset_y):
    col = (mx + offset_x) // GAP
    row = ((my - TOPBAR_HEIGHT) + offset_y) // GAP
    return col, row

def draw_grid(surface, offset_x, offset_y, now, hover_pos=None, selected_crop=None):
    # Добавляем запас по 2 клетки с каждой стороны
    cols = SCREEN_WIDTH // GAP + 6
    rows = (SCREEN_HEIGHT - TOPBAR_HEIGHT) // GAP + 6
    for col in range(cols):
        for row in range(rows):
            x = col * GAP - offset_x % GAP - 2 * GAP
            y = row * GAP - offset_y % GAP + TOPBAR_HEIGHT - 2 * GAP
            grid_pos = ((col + offset_x // GAP - 2), (row + offset_y // GAP - 2))
            rect = (x, y, SQUARE_SIZE, SQUARE_SIZE)
            # Подсветка по наведению
            if hover_pos and grid_pos == hover_pos and selected_crop:
                base_color = selected_crop.plant_color
                pale_color = tuple(min(255, int(c + (255 - c) * 0.6)) for c in base_color)
                pygame.draw.rect(surface, pale_color, rect)
            elif grid_pos in field:
                crop_info = field[grid_pos]
                crop = crop_info["crop"]
                plant_time = crop_info["plant_time"]
                state = crop_info["state"]
                if state == "planted" and now - plant_time >= crop.grow_time:
                    crop_info["state"] = "ready"
                    state = "ready"
                pygame.draw.rect(surface, crop.get_color(state), rect)
            else:
                pygame.draw.rect(surface, SQUARE_COLOR, rect)
            pygame.draw.rect(surface, (100, 70, 40), rect, 2)

def draw_topbar(surface, font, selected_crop):
    # Создаем поверхность с поддержкой прозрачности
    island_surface = pygame.Surface((290, 40), pygame.SRCALPHA)
    
    # Заполняем полупрозрачным цветом с округлыми краями
    pygame.draw.rect(island_surface, (230, 230, 230, 180), (0, 0, 290, 40), border_radius=20)
    
    # Позиционируем островок по центру
    island_x = (SCREEN_WIDTH - 290) // 2
    island_y = 10
    
    # Рисуем границу с округлыми краями
    pygame.draw.rect(island_surface, (180, 180, 180, 255), (0, 0, 290, 40), 2, border_radius=20)
    
    # Рендерим текст
    crop_text = font.render(f"Культура: {selected_crop.name}", True, FONT_COLOR)
    text_rect = crop_text.get_rect(center=(290 // 2, 40 // 2))
    island_surface.blit(crop_text, text_rect)
    
    # Накладываем островок на основную поверхность
    surface.blit(island_surface, (island_x, island_y))

def draw_coordinates(surface, font, mx, my, offset_x, offset_y):
    # Получаем координаты квадрата под курсором
    col = (mx + offset_x) // GAP
    row = ((my - TOPBAR_HEIGHT) + offset_y) // GAP
    
    # Создаем поверхность для координат
    coords_surface = pygame.Surface((120, 70), pygame.SRCALPHA)
    pygame.draw.rect(coords_surface, COORDS_BG, (0, 0, 120, 70), border_radius=10)
    
    # Рендерим каждую координату отдельно
    x_text = font.render(f"X: {col}", True, COORDS_COLOR)
    y_text = font.render(f"Y: {row}", True, COORDS_COLOR)
    
    # Позиционируем текст по центру поверхности
    x_rect = x_text.get_rect(centerx=120 // 2, centery=20)
    y_rect = y_text.get_rect(centerx=120 // 2, centery=50)
    
    coords_surface.blit(x_text, x_rect)
    coords_surface.blit(y_text, y_rect)
    
    # Размещаем в левом верхнем углу
    surface.blit(coords_surface, (10, 10))

def draw_stats(surface, font, money, harvest):
    # Загружаем иконки
    try:
        money_icon = pygame.image.load(MONEY_ICON)
        money_icon = pygame.transform.scale(money_icon, (24, 24))
        harvest_icon = pygame.image.load(HARVEST_ICON)
        harvest_icon = pygame.transform.scale(harvest_icon, (24, 24))
    except:
        print("Ошибка загрузки иконок")
        return

    # Создаем поверхности
    money_surface = pygame.Surface((200, 40), pygame.SRCALPHA)
    harvest_surface = pygame.Surface((200, 40), pygame.SRCALPHA)

    # Рисуем фон
    pygame.draw.rect(money_surface, (230, 230, 230, 180), (0, 0, 200, 40), border_radius=20)
    pygame.draw.rect(money_surface, (180, 180, 180, 255), (0, 0, 200, 40), 2, border_radius=20)
    pygame.draw.rect(harvest_surface, (230, 230, 230, 180), (0, 0, 200, 40), border_radius=20)
    pygame.draw.rect(harvest_surface, (180, 180, 180, 255), (0, 0, 200, 40), 2, border_radius=20)

    # Размещаем иконки
    money_surface.blit(money_icon, (10, 8))
    harvest_surface.blit(harvest_icon, (10, 8))

    # Рендерим текст
    money_text = font.render(str(money), True, FONT_COLOR)
    harvest_text = font.render(str(harvest), True, FONT_COLOR)
    
    # Позиционируем текст после иконок
    money_rect = money_text.get_rect(midleft=(44, 20))
    harvest_rect = harvest_text.get_rect(midleft=(44, 20))
    
    money_surface.blit(money_text, money_rect)
    harvest_surface.blit(harvest_text, harvest_rect)
    
    # Размещаем островки
    surface.blit(money_surface, (SCREEN_WIDTH - 210, 10))
    surface.blit(harvest_surface, (SCREEN_WIDTH - 210, 60))

def main():
    global selected_crop_idx
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Farmer in Field")
    clock = pygame.time.Clock()
    
    # Попытка загрузить шрифт с поддержкой Unicode
    try:
        # Сначала пробуем использовать стандартный шрифт pygame
        font = pygame.font.Font(None, 32)
    except:
        try:
            # Если не получилось, пробуем системные шрифты
            font = pygame.font.SysFont("arial", 32)
        except:
            print("Ошибка: Не удалось загрузить шрифт")
            pygame.quit()
            sys.exit()

    offset_x, offset_y = 0, 0
    money = 0
    harvest = 0
    show_coords = False
    
    while True:
        now = time.time()
        hover_pos = None
        mx, my = pygame.mouse.get_pos()
        if my > TOPBAR_HEIGHT:  # Убрана проверка menu_open
            col, row = get_square_by_pos(mx, my, offset_x, offset_y)
            hover_pos = (col, row)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEWHEEL:
                selected_crop_idx = (selected_crop_idx + event.y) % len(CROPS)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if my > TOPBAR_HEIGHT:  # Убрана проверка menu_open
                    col, row = get_square_by_pos(mx, my, offset_x, offset_y)
                    grid_pos = (col, row)
                    selected_crop = CROPS[selected_crop_idx]
                    if grid_pos not in field:
                        field[grid_pos] = {"crop": selected_crop, "plant_time": now, "state": "planted"}
                    elif field[grid_pos]["state"] == "ready":
                        harvest += field[grid_pos]["crop"].yield_count
                        del field[grid_pos]
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    show_coords = not show_coords

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            offset_x -= 5
        if keys[pygame.K_RIGHT]:
            offset_x += 5
        if keys[pygame.K_UP]:
            offset_y -= 5
        if keys[pygame.K_DOWN]:
            offset_y += 5

        screen.fill(BG_COLOR)
        draw_grid(screen, offset_x, offset_y, now, hover_pos, CROPS[selected_crop_idx])
        draw_topbar(screen, font, CROPS[selected_crop_idx])
        draw_stats(screen, font, money, harvest)  # Добавьте эту строку
        if show_coords:
            mx, my = pygame.mouse.get_pos()
            draw_coordinates(screen, font, mx, my, offset_x, offset_y)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()