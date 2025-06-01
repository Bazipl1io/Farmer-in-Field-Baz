# -*- coding: utf-8 -*-
import pygame
import sys
import time
import os
import json

# Пути к иконкам
ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
MONEY_ICON = os.path.join(ICONS_DIR, "monay.png")
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

TOMATO_COLOR = (255, 0, 0)
TOMATO_READY_COLOR = (184, 20, 20)

FONT_COLOR = (0, 0, 0)
MENU_WIDTH = 300
MENU_BG = (255, 255, 255, 180)  # Прозрачный белый
TOPBAR_HEIGHT = 40
TOPBAR_BG = (230, 230, 230)
COORDS_COLOR = (255, 255, 255)
COORDS_BG = (0, 0, 0, 180)
MENU_OVERLAY_ALPHA = 0 # Затемнение заднего фона меню

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
        
# Культура: капуста
class Tomato:
    name = "Помидор"
    plant_color = TOMATO_COLOR
    ready_color = TOMATO_READY_COLOR
    grow_time = 15  # секунд
    yield_count = 2

    @staticmethod
    def get_color(state):
        return Tomato.ready_color if state == "ready" else Tomato.plant_color

# Добавьте сюда новые культуры по аналогии

CROPS = [Carrot, Cabbage, Tomato]
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

def draw_shop(surface, font, harvest, price, sell_count):
    shop_width, shop_height = 400, 250
    shop_x = (SCREEN_WIDTH - shop_width) // 2
    shop_y = (SCREEN_HEIGHT - shop_height) // 2

    shop_surface = pygame.Surface((shop_width, shop_height), pygame.SRCALPHA)
    pygame.draw.rect(shop_surface, (255, 255, 255, 240), (0, 0, shop_width, shop_height), border_radius=20)
    pygame.draw.rect(shop_surface, (180, 180, 180, 255), (0, 0, shop_width, shop_height), 2, border_radius=20)

    title = font.render("Магазин", True, (0, 0, 0))
    title_rect = title.get_rect(center=(shop_width // 2, 40))
    shop_surface.blit(title, title_rect)

    info = font.render(f"Урожай: {harvest}", True, (0, 0, 0))
    info_rect = info.get_rect(center=(shop_width // 2, 90))
    shop_surface.blit(info, info_rect)

    price_text = font.render(f"Цена: {price} за 1", True, (0, 0, 0))
    price_rect = price_text.get_rect(center=(shop_width // 2, 130))
    shop_surface.blit(price_text, price_rect)

    count_text = font.render(f"Продать: {sell_count}", True, (0, 0, 0))
    count_rect = count_text.get_rect(center=(shop_width // 2, 170))
    shop_surface.blit(count_text, count_rect)

    # Кнопки + и -
    btn_w, btn_h = 40, 40
    minus_rect = pygame.Rect(90, 150, btn_w, btn_h)
    plus_rect = pygame.Rect(shop_width - 90 - btn_w, 150, btn_w, btn_h)
    pygame.draw.rect(shop_surface, (230, 230, 230), minus_rect, border_radius=10)
    pygame.draw.rect(shop_surface, (180, 180, 180), minus_rect, 2, border_radius=10)
    pygame.draw.rect(shop_surface, (230, 230, 230), plus_rect, border_radius=10)
    pygame.draw.rect(shop_surface, (180, 180, 180), plus_rect, 2, border_radius=10)
    minus_sign = font.render("-", True, (0, 0, 0))
    plus_sign = font.render("+", True, (0, 0, 0))
    shop_surface.blit(minus_sign, minus_sign.get_rect(center=minus_rect.center))
    shop_surface.blit(plus_sign, plus_sign.get_rect(center=plus_rect.center))

    # Кнопка "Продать"
    sell_btn_rect = pygame.Rect((shop_width - 220)//2, 210, 220, 36)
    pygame.draw.rect(shop_surface, (230, 230, 230), sell_btn_rect, border_radius=12)
    pygame.draw.rect(shop_surface, (180, 180, 180), sell_btn_rect, 2, border_radius=12)
    sell_text = font.render("Продать", True, (0, 0, 0))
    shop_surface.blit(sell_text, sell_text.get_rect(center=sell_btn_rect.center))

    # Крестик (закрыть)
    close_rect = pygame.Rect(shop_width - 44, 12, 32, 32)
    pygame.draw.rect(shop_surface, (230, 230, 230, 220), close_rect, border_radius=10)
    pygame.draw.rect(shop_surface, (180, 180, 180), close_rect, 2, border_radius=10)
    x_text = font.render("×", True, (80, 80, 80))
    shop_surface.blit(x_text, x_text.get_rect(center=close_rect.center))

    surface.blit(shop_surface, (shop_x, shop_y))

    # Вернуть абсолютные координаты кнопок
    minus_abs = pygame.Rect(shop_x + minus_rect.x, shop_y + minus_rect.y, btn_w, btn_h)
    plus_abs = pygame.Rect(shop_x + plus_rect.x, shop_y + plus_rect.y, btn_w, btn_h)
    sell_abs = pygame.Rect(shop_x + sell_btn_rect.x, shop_y + sell_btn_rect.y, sell_btn_rect.width, sell_btn_rect.height)
    close_abs = pygame.Rect(shop_x + close_rect.x, shop_y + close_rect.y, close_rect.width, close_rect.height)
    return minus_abs, plus_abs, sell_abs, close_abs

def draw_menu(surface, font):
    menu_width, menu_height = 400, 320
    menu_x = (SCREEN_WIDTH - menu_width) // 2
    menu_y = (SCREEN_HEIGHT - menu_height) // 2

    menu_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
    pygame.draw.rect(menu_surface, (255, 255, 255, 240), (0, 0, menu_width, menu_height), border_radius=20)
    pygame.draw.rect(menu_surface, (180, 180, 180, 255), (0, 0, menu_width, menu_height), 2, border_radius=20)

    title = font.render("Меню", True, (0, 0, 0))
    title_rect = title.get_rect(center=(menu_width // 2, 50))
    menu_surface.blit(title, title_rect)

    btn_w, btn_h = 220, 50
    btn1_rect = pygame.Rect((menu_width - btn_w)//2, 100, btn_w, btn_h)
    btn2_rect = pygame.Rect((menu_width - btn_w)//2, 170, btn_w, btn_h)
    btn3_rect = pygame.Rect((menu_width - btn_w)//2, 240, btn_w, btn_h)  # Магазин

    pygame.draw.rect(menu_surface, (230, 230, 230), btn1_rect, border_radius=12)
    pygame.draw.rect(menu_surface, (180, 180, 180), btn1_rect, 2, border_radius=12)
    pygame.draw.rect(menu_surface, (230, 230, 230), btn2_rect, border_radius=12)
    pygame.draw.rect(menu_surface, (180, 180, 180), btn2_rect, 2, border_radius=12)
    pygame.draw.rect(menu_surface, (230, 230, 230), btn3_rect, border_radius=12)
    pygame.draw.rect(menu_surface, (180, 180, 180), btn3_rect, 2, border_radius=12)

    btn1_text = font.render("Вернуться в игру", True, (0, 0, 0))
    btn2_text = font.render("Выйти", True, (0, 0, 0))
    btn3_text = font.render("Магазин", True, (0, 0, 0))
    menu_surface.blit(btn1_text, btn1_text.get_rect(center=btn1_rect.center))
    menu_surface.blit(btn2_text, btn2_text.get_rect(center=btn2_rect.center))
    menu_surface.blit(btn3_text, btn3_text.get_rect(center=btn3_rect.center))

    burger_rect = pygame.Rect(16, 12, 44, 36)
    pygame.draw.rect(menu_surface, (230, 230, 230, 220), burger_rect, border_radius=10)
    pygame.draw.rect(menu_surface, (180, 180, 180), burger_rect, 2, border_radius=10)
    for i in range(3):
        y = 20 + i * 10
        pygame.draw.rect(menu_surface, (80, 80, 80), (24, y, 28, 4), border_radius=2)

    surface.blit(menu_surface, (menu_x, menu_y))

    btn1_abs = pygame.Rect(menu_x + btn1_rect.x, menu_y + btn1_rect.y, btn_w, btn_h)
    btn2_abs = pygame.Rect(menu_x + btn2_rect.x, menu_y + btn2_rect.y, btn_w, btn_h)
    btn3_abs = pygame.Rect(menu_x + btn3_rect.x, menu_y + btn3_rect.y, btn_w, btn_h)
    burger_abs = pygame.Rect(menu_x + burger_rect.x, menu_y + burger_rect.y, burger_rect.width, burger_rect.height)
    return btn1_abs, btn2_abs, btn3_abs, burger_abs

def draw_menu_button(surface):
    btn_rect = pygame.Rect(16, 12, 44, 36)
    # Кнопка с закруглениями
    pygame.draw.rect(surface, (230, 230, 230, 220), btn_rect, border_radius=10)
    pygame.draw.rect(surface, (180, 180, 180), btn_rect, 2, border_radius=10)
    # "Бургер" иконка
    for i in range(3):
        y = 20 + i * 10
        pygame.draw.rect(surface, (80, 80, 80), (24, y, 28, 4), border_radius=2)
    return btn_rect

PLAYER_SAVE_FILE = "save_player.json"
FIELD_SAVE_FILE = "save_field.json"
ENCRYPTED_SAVE_FILE = "save_encrypted.dat"
ENCRYPTION_KEY = "my_secret_key_123"  # Можно сделать любой

def save_player(money, harvest):
    data = {
        "money": money,
        "harvest": harvest
    }
    with open(PLAYER_SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_player():
    if not os.path.exists(PLAYER_SAVE_FILE):
        return 0, 0
    with open(PLAYER_SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("money", 0), data.get("harvest", 0)

def save_field(field, offset_x, offset_y):
    data = {
        "offset_x": offset_x,
        "offset_y": offset_y,
        "field": [
            {
                "col": col,
                "row": row,
                "crop": crop_info["crop"].__name__,
                "plant_time": crop_info["plant_time"],
                "state": crop_info["state"]
            }
            for (col, row), crop_info in field.items()
        ]
    }
    with open(FIELD_SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_field():
    if not os.path.exists(FIELD_SAVE_FILE):
        return {}, 0, 0
    with open(FIELD_SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    crops_by_name = {cls.__name__: cls for cls in CROPS}
    field = {}
    for item in data.get("field", []):
        crop_cls = crops_by_name.get(item["crop"])
        if crop_cls:
            field[(item["col"], item["row"])] = {
                "crop": crop_cls,
                "plant_time": item["plant_time"],
                "state": item["state"]
            }
    return field, data.get("offset_x", 0), data.get("offset_y", 0)

def xor_crypt(data: bytes, key: str) -> bytes:
    key_bytes = key.encode("utf-8")
    return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])

def save_encrypted(money, harvest, field, offset_x, offset_y, cheater=False):
    # Сохраняем всё в одну структуру
    data = {
        "money": money,
        "harvest": harvest,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "cheater": cheater,  # Новое поле
        "field": [
            {
                "col": col,
                "row": row,
                "crop": crop_info["crop"].__name__,
                "plant_time": crop_info["plant_time"],
                "state": crop_info["state"]
            }
            for (col, row), crop_info in field.items()
        ]
    }
    json_data = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    encrypted = xor_crypt(json_data, ENCRYPTION_KEY)
    with open(ENCRYPTED_SAVE_FILE, "wb") as f:
        f.write(encrypted)

def check_cheater(money, harvest, field, offset_x, offset_y):
    enc = load_encrypted()
    if not enc:
        return False
    # Сравниваем все значения
    if enc.get("money", 0) != money: return True
    if enc.get("harvest", 0) != harvest: return True
    if enc.get("offset_x", 0) != offset_x: return True
    if enc.get("offset_y", 0) != offset_y: return True
    # Сравниваем поле
    field_list = [
        {
            "col": col,
            "row": row,
            "crop": crop_info["crop"].__name__,
            "plant_time": crop_info["plant_time"],
            "state": crop_info["state"]
        }
        for (col, row), crop_info in field.items()
    ]
    # Сортируем для корректного сравнения
    def sort_key(item): return (item["col"], item["row"], item["crop"])
    if sorted(enc.get("field", []), key=sort_key) != sorted(field_list, key=sort_key):
        return True
    return enc.get("cheater", False)  # Если уже было клеймо, возвращаем True

def load_encrypted():
    if not os.path.exists(ENCRYPTED_SAVE_FILE):
        return None
    with open(ENCRYPTED_SAVE_FILE, "rb") as f:
        encrypted = f.read()
    decrypted = xor_crypt(encrypted, ENCRYPTION_KEY)
    try:
        data = json.loads(decrypted.decode("utf-8"))
    except Exception:
        return None
    return data

def main():
    global selected_crop_idx, SCREEN_WIDTH, SCREEN_HEIGHT, field
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Farmer in Field")
    clock = pygame.time.Clock()
    fullscreen = False

    try:
        font = pygame.font.Font(None, 32)
    except:
        try:
            font = pygame.font.SysFont("arial", 32)
        except:
            print("Ошибка: Не удалось загрузить шрифт")
            pygame.quit()
            sys.exit()

    # Загрузка двух частей
    money, harvest = load_player()
    field, offset_x, offset_y = load_field()

    # Проверка на читерство
    cheater = check_cheater(money, harvest, field, offset_x, offset_y)
    cheater_time = time.time() if cheater else None  # время появления надписи

    # Если обнаружен читер — ставим клеймо в зашифрованном сейве
    if cheater:
        save_encrypted(money, harvest, field, offset_x, offset_y, cheater=True)

    show_coords = False
    menu_open = False
    shop_open = False
    shop_price = 10
    shop_sell_count = 1

    game_time = 0
    last_real_time = time.time()

    while True:
        real_now = time.time()
        if not menu_open and not shop_open:
            delta = real_now - last_real_time
            game_time += delta
        last_real_time = real_now

        now = game_time

        hover_pos = None
        mx, my = pygame.mouse.get_pos()
        if not menu_open and not shop_open and my > TOPBAR_HEIGHT:
            col, row = get_square_by_pos(mx, my, offset_x, offset_y)
            hover_pos = (col, row)

        menu_btn_rect = None
        if not menu_open and not shop_open:
            screen.fill(BG_COLOR)
            draw_grid(screen, offset_x, offset_y, now, hover_pos, CROPS[selected_crop_idx])
            draw_topbar(screen, font, CROPS[selected_crop_idx])
            draw_stats(screen, font, money, harvest)
            menu_btn_rect = draw_menu_button(screen)
            if show_coords:
                mx, my = pygame.mouse.get_pos()
                draw_coordinates(screen, font, mx, my, offset_x, offset_y)
            # Показываем "ЧИТЕР" если надо (полупрозрачная и исчезает через 10 сек)
            if cheater and cheater_time and (real_now - cheater_time < 10):
                cheat_font = pygame.font.Font(None, 80)
                cheat_text = cheat_font.render("ЧИТЕР", True, (255, 0, 0))
                cheat_surface = pygame.Surface(cheat_text.get_size(), pygame.SRCALPHA)
                cheat_surface.blit(cheat_text, (0, 0))
                cheat_surface.set_alpha(120)  # полупрозрачность
                cheat_rect = cheat_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                screen.blit(cheat_surface, cheat_rect)
            elif cheater and cheater_time and (real_now - cheater_time >= 10):
                cheater = False  # убрать надпись после 10 секунд
                cheater_time = None
        elif menu_open:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, MENU_OVERLAY_ALPHA))
            screen.blit(overlay, (0, 0))
            btn1, btn2, btn3, burger = draw_menu(screen, font)
        elif shop_open:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, MENU_OVERLAY_ALPHA))
            screen.blit(overlay, (0, 0))
            minus_btn, plus_btn, sell_btn, close_btn = draw_shop(screen, font, harvest, shop_price, shop_sell_count)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_player(money, harvest)
                save_field(field, offset_x, offset_y)
                # Передаем клеймо если оно есть
                enc = load_encrypted()
                is_cheater = enc.get("cheater", False) if enc else False
                save_encrypted(money, harvest, field, offset_x, offset_y, cheater=is_cheater or cheater)
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if shop_open:
                        shop_open = False
                    else:
                        menu_open = not menu_open
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        info = pygame.display.Info()
                        SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.NOFRAME)
                    else:
                        SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                if not menu_open and not shop_open and event.key == pygame.K_F3:
                    show_coords = not show_coords
                # Сохранение по S, загрузка по L
                if event.key == pygame.K_s:
                    save_player(money, harvest)
                    save_field(field, offset_x, offset_y)
                    enc = load_encrypted()
                    is_cheater = enc.get("cheater", False) if enc else False
                    save_encrypted(money, harvest, field, offset_x, offset_y, cheater=is_cheater or cheater)
                if event.key == pygame.K_l:
                    money, harvest = load_player()
                    field, offset_x, offset_y = load_field()
                    cheater = check_cheater(money, harvest, field, offset_x, offset_y)
                    cheater_time = time.time() if cheater else None
                    # Если обнаружен читер — ставим клеймо в зашифрованном сейве
                    if cheater:
                        save_encrypted(money, harvest, field, offset_x, offset_y, cheater=True)
            if not menu_open and not shop_open:
                if event.type == pygame.MOUSEWHEEL:
                    selected_crop_idx = (selected_crop_idx + event.y) % len(CROPS)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if menu_btn_rect and menu_btn_rect.collidepoint(mx, my):
                        menu_open = True
                    elif my > TOPBAR_HEIGHT:
                        col, row = get_square_by_pos(mx, my, offset_x, offset_y)
                        grid_pos = (col, row)
                        selected_crop = CROPS[selected_crop_idx]
                        if grid_pos not in field:
                            field[grid_pos] = {"crop": selected_crop, "plant_time": now, "state": "planted"}
                        elif field[grid_pos]["state"] == "ready":
                            harvest += field[grid_pos]["crop"].yield_count
                            del field[grid_pos]
            elif menu_open:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    btn1, btn2, btn3, burger = draw_menu(screen, font)
                    if btn1.collidepoint(mx, my) or burger.collidepoint(mx, my):
                        menu_open = False
                    elif btn2.collidepoint(mx, my):
                        pygame.quit()
                        sys.exit()
                    elif btn3.collidepoint(mx, my):
                        menu_open = False
                        shop_open = True
                        shop_sell_count = 1
            elif shop_open:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    minus_btn, plus_btn, sell_btn, close_btn = draw_shop(screen, font, harvest, shop_price, shop_sell_count)
                    if minus_btn.collidepoint(mx, my):
                        if shop_sell_count > 1:
                            shop_sell_count -= 1
                    elif plus_btn.collidepoint(mx, my):
                        if shop_sell_count < min(10, harvest):
                            shop_sell_count += 1
                    elif sell_btn.collidepoint(mx, my):
                        if harvest >= shop_sell_count:
                            harvest -= shop_sell_count
                            money += shop_sell_count * shop_price
                            shop_sell_count = min(shop_sell_count, harvest) if harvest > 0 else 1
                    elif close_btn.collidepoint(mx, my):
                        shop_open = False

        if not menu_open and not shop_open:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                offset_x -= 5
            if keys[pygame.K_RIGHT]:
                offset_x += 5
            if keys[pygame.K_UP]:
                offset_y -= 5
            if keys[pygame.K_DOWN]:
                offset_y += 5

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()