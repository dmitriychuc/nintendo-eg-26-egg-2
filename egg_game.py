import sys
import random
import math
import pygame

# -------------------------
# Константы
# -------------------------
SCREEN_W, SCREEN_H = 720, 600
FPS_BASE = 60

# Цвета
BACKGROUND_COLOR = (25, 25, 35)
LINE_COLOR = (70, 100, 150)
EGG_COLOR = (245, 240, 200)
EGG_SHINE = (255, 250, 220)
WOLF_COLOR = (210, 210, 230)
WOLF_SHADOW = (180, 180, 200)
TEXT_COLOR = (230, 230, 255)
TEXT_SHADOW = (150, 150, 180)
DANGER_COLOR = (220, 80, 80)
OK_COLOR = (100, 200, 120)
UI_COLOR = (80, 120, 180)
UI_HIGHLIGHT = (120, 160, 220)

# Новые цвета для визуальных улучшений
STAR_COLORS = [(200, 200, 255), (180, 180, 240), (160, 160, 220)]
CLOUD_COLORS = [(60, 60, 80), (70, 70, 90), (80, 80, 100)]

MISS_TO_GAMEOVER = 3
SPAWN_BASE_MS = 1200
SPAWN_MIN_MS = 380
SPEED_BASE = 0.22
SPEED_MAX = 0.55

POS_LEFT_TOP, POS_RIGHT_TOP, POS_LEFT_BOTTOM, POS_RIGHT_BOTTOM = 0, 1, 2, 3

# -------------------------
# Вспомогательные функции
# -------------------------
def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(color1, color2, t):
    return (
        int(color1[0] + (color2[0] - color1[0]) * t),
        int(color1[1] + (color2[1] - color1[1]) * t),
        int(color1[2] + (color2[2] - color1[2]) * t)
    )

def lerp2(p1, p2, t):
    return (lerp(p1[0], p2[0], t), lerp(p1[1], p2[1], t))

def polyline_point(points, t):
    if t <= 0:
        return points[0]
    if t >= 1:
        return points[-1]
    n = len(points) - 1
    seg = t * n
    i = int(seg)
    local_t = seg - i
    return lerp2(points[i], points[i + 1], local_t)

def make_chutes():
    lt = [(90, 40), (120, 70), (160, 110), (210, 150), (240, 180)]
    rt = [(SCREEN_W - 90, 40), (SCREEN_W - 120, 70), (SCREEN_W - 160, 110), (SCREEN_W - 210, 150), (SCREEN_W - 240, 180)]
    lb = [(90, SCREEN_H - 120), (120, SCREEN_H - 100), (160, SCREEN_H - 80), (200, SCREEN_H - 70), (240, SCREEN_H - 60)]
    rb = [(SCREEN_W - 90, SCREEN_H - 120), (SCREEN_W - 120, SCREEN_H - 100), (SCREEN_W - 160, SCREEN_H - 80), (SCREEN_W - 200, SCREEN_H - 70), (SCREEN_W - 240, SCREEN_H - 60)]

    catch_lt = (255, 170)
    catch_rt = (SCREEN_W - 255, 170)
    catch_lb = (255, SCREEN_H - 58)
    catch_rb = (SCREEN_W - 255, SCREEN_H - 58)

    lt2 = lt[:-1] + [catch_lt]
    rt2 = rt[:-1] + [catch_rt]
    lb2 = lb[:-1] + [catch_lb]
    rb2 = rb[:-1] + [catch_rb]

    return {
        POS_LEFT_TOP: {"points": lt2, "catch": catch_lt},
        POS_RIGHT_TOP: {"points": rt2, "catch": catch_rt},
        POS_LEFT_BOTTOM: {"points": lb2, "catch": catch_lb},
        POS_RIGHT_BOTTOM: {"points": rb2, "catch": catch_rb},
    }

# -------------------------
# Частицы эффектов
# -------------------------
class Particle:
    def __init__(self, x, y, color, velocity=None, size=3, life=1.0):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, size)
        self.life = life
        self.max_life = life
        self.velocity = velocity or (random.uniform(-2, 2), random.uniform(-3, 0))
        self.rotation = random.uniform(0, 360)
        self.rotate_speed = random.uniform(-5, 5)
        
    def update(self, dt):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.velocity = (self.velocity[0] * 0.95, self.velocity[1] + 0.2)
        self.life -= dt
        self.rotation += self.rotate_speed * dt
        return self.life > 0
        
    def draw(self, surf):
        alpha = int(255 * (self.life / self.max_life))
        size = int(self.size * (self.life / self.max_life))
        if size > 0:
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            
            # Разные формы частиц
            if random.random() > 0.7:
                # Звездообразная частица
                points = []
                for i in range(5):
                    angle = self.rotation + i * 72
                    rad = math.radians(angle)
                    points.append((size + math.cos(rad) * size, 
                                  size + math.sin(rad) * size))
                pygame.draw.polygon(s, (*self.color, alpha), points)
            else:
                # Круглая частица
                pygame.draw.circle(s, (*self.color, alpha), (size, size), size)
                
            surf.blit(s, (int(self.x - size), int(self.y - size)))

# -------------------------
# Яйцо с эффектами
# -------------------------
class Egg:
    def __init__(self, chute_id, chutes, speed):
        self.chute_id = chute_id
        self.path = chutes[chute_id]["points"]
        self.t = 0.0
        self.speed = speed
        self.caught = False
        self.dead = False
        self.rotation = random.uniform(0, 360)
        self.rotate_speed = random.uniform(-2, 2)
        self.trail = []  # След за яйцом
        
    def update(self, dt):
        if self.dead:
            return
        
        # Сохраняем позицию для следа
        if len(self.trail) < 5:
            self.trail.append(self.pos())
        else:
            self.trail.pop(0)
            self.trail.append(self.pos())
            
        self.t += self.speed * dt
        self.rotation += self.rotate_speed
        if self.t >= 1.0:
            self.t = 1.0

    def pos(self):
        return polyline_point(self.path, self.t)
    
    def draw(self, surf):
        x, y = self.pos()
        
        # Рисуем след
        for i, pos in enumerate(self.trail):
            alpha = i * 50  # Прозрачность уменьшается для более старых позиций
            size = 5 - i  # Размер уменьшается
            if size > 0:
                s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*EGG_COLOR, alpha), (size, size), size)
                surf.blit(s, (int(pos[0] - size), int(pos[1] - size)))
        
        # Свечение яйца
        glow_size = 12
        s = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*EGG_SHINE, 100), (glow_size, glow_size), glow_size)
        surf.blit(s, (int(x - glow_size), int(y - glow_size)))
        
        # Блеск на яйце
        angle_rad = math.radians(self.rotation)
        shine_x = x + math.cos(angle_rad) * 4
        shine_y = y + math.sin(angle_rad) * 3
        
        # Основное яйцо
        pygame.draw.circle(surf, EGG_COLOR, (int(x), int(y)), 8)
        # Блеск
        pygame.draw.circle(surf, EGG_SHINE, (int(shine_x), int(shine_y)), 3)

# -------------------------
# Игрок (волк) с анимацией
# -------------------------
class Wolf:
    def __init__(self):
        self.position = POS_LEFT_BOTTOM
        self.animation_timer = 0
        self.catch_animation = 0
        
    def set_position(self, pos):
        self.position = pos
        
    def trigger_catch(self):
        self.catch_animation = 1.0
        
    def update(self, dt):
        self.animation_timer += dt
        if self.catch_animation > 0:
            self.catch_animation -= dt * 3
            
    def draw(self, surf):
        cx, cy = SCREEN_W // 2, SCREEN_H // 2 + 10
        
        # Анимация тела волка
        bounce = math.sin(self.animation_timer * 3) * 2
        body_rect = pygame.Rect(0, 0, 64, 90)
        body_rect.center = (cx, cy + bounce)
        
        # Тень тела
        pygame.draw.rect(surf, WOLF_SHADOW, body_rect.move(2, 2), border_radius=10)
        # Основное тело
        pygame.draw.rect(surf, WOLF_COLOR, body_rect, border_radius=10)
        
        # Уши
        ear_left = (cx - 20, cy - 35 + bounce)
        ear_right = (cx + 20, cy - 35 + bounce)
        pygame.draw.circle(surf, WOLF_SHADOW, ear_left, 10)
        pygame.draw.circle(surf, WOLF_SHADOW, ear_right, 10)
        pygame.draw.circle(surf, WOLF_COLOR, (cx - 20, cy - 35 + bounce), 8)
        pygame.draw.circle(surf, WOLF_COLOR, (cx + 20, cy - 35 + bounce), 8)
        
        # Морда
        pygame.draw.circle(surf, WOLF_COLOR, (cx, cy - 5 + bounce), 35)
        
        # Глаза
        eye_y = cy - 15 + bounce
        pygame.draw.circle(surf, (50, 50, 70), (cx - 12, eye_y), 6)
        pygame.draw.circle(surf, (50, 50, 70), (cx + 12, eye_y), 6)
        
        # Зрачки с анимацией
        pupil_dx = math.sin(self.animation_timer * 2) * 2
        pygame.draw.circle(surf, (220, 220, 240), (cx - 12 + pupil_dx, eye_y), 3)
        pygame.draw.circle(surf, (220, 220, 240), (cx + 12 + pupil_dx, eye_y), 3)
        
        # Нос
        pygame.draw.circle(surf, (80, 80, 100), (cx, cy + 5 + bounce), 8)
        
        # Улыбка
        smile_y = cy + 15 + bounce
        pygame.draw.arc(surf, (80, 80, 100), (cx - 15, smile_y - 10, 30, 20), 0.2, 2.9, 2)
        
        # Анимация ловли
        catch_scale = 1.0 + self.catch_animation * 0.3
        
        # Корзины для ловли
        baskets = {
            POS_LEFT_TOP: (255, 170),
            POS_RIGHT_TOP: (SCREEN_W - 255, 170),
            POS_LEFT_BOTTOM: (255, SCREEN_H - 58),
            POS_RIGHT_BOTTOM: (SCREEN_W - 255, SCREEN_H - 58),
        }
        
        for pos_id, p in baskets.items():
            is_active = pos_id == self.position
            color = OK_COLOR if is_active else LINE_COLOR
            size = 16 if is_active else 14
            
            # Подсветка активной позиции
            if is_active:
                glow_size = size + 4
                s = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*OK_COLOR, 100), (glow_size, glow_size), glow_size)
                surf.blit(s, (p[0] - glow_size, p[1] - glow_size))
            
            # Корзина
            pygame.draw.circle(surf, color, p, int(size * catch_scale), 3)
            
            # Ручка корзины
            if is_active:
                pygame.draw.arc(surf, color, (p[0]-10, p[1]-12, 20, 10), 3.14, 6.28, 2)

# -------------------------
# Класс кнопки
# -------------------------
class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        self.clicked = False
        self.animation = 0  # 0-1 значение для анимации
        
    def update(self, mouse_pos, mouse_click):
        was_hovered = self.hovered
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        # Анимация при наведении
        if self.hovered and not was_hovered:
            self.animation = 0  # Начинаем анимацию
        elif not self.hovered and was_hovered:
            self.animation = 1  # Начинаем обратную анимацию
            
        if self.animation < 1 and self.hovered:
            self.animation += 0.1
        elif self.animation > 0 and not self.hovered:
            self.animation -= 0.1
            
        if self.hovered and mouse_click:
            if self.action:
                self.action()
            self.clicked = True
            return True
        return False
        
    def draw(self, surf, font):
        # Интерполяция цвета и размера на основе анимации
        color = lerp_color(UI_COLOR, UI_HIGHLIGHT, self.animation)
        scale = 1.0 + self.animation * 0.05
        
        # Масштабированный прямоугольник
        scaled_rect = pygame.Rect(
            self.rect.centerx - self.rect.width * scale / 2,
            self.rect.centery - self.rect.height * scale / 2,
            self.rect.width * scale,
            self.rect.height * scale
        )
        
        pygame.draw.rect(surf, color, scaled_rect, border_radius=8)
        pygame.draw.rect(surf, TEXT_COLOR, scaled_rect, 2, border_radius=8)
        
        text_surf = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surf.blit(text_surf, text_rect)

# -------------------------
# Игра с улучшенным интерфейсом
# -------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("🐺 EG-26 Egg Catcher - Nintendo Style")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        
        # Шрифты
        self.font_small = pygame.font.SysFont("Arial", 16)
        self.font = pygame.font.SysFont("Arial", 22)
        self.font_big = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 40, bold=True)
        
        self.chutes = make_chutes()
        self.eggs = []
        self.particles = []
        self.wolf = Wolf()
        
        self.score = 0
        self.misses = 0
        self.game_over = False
        self.paused = False
        self.show_menu = True
        
        self.spawn_timer = 0.0
        self.spawn_interval_ms = SPAWN_BASE_MS
        self.difficulty_meter = 0.0
        self.combo = 0
        self.combo_timer = 0
        
        # Анимированный фон
        self.stars = []
        for _ in range(50):
            self.stars.append({
                'x': random.randint(0, SCREEN_W),
                'y': random.randint(0, SCREEN_H),
                'size': random.randint(1, 3),
                'speed': random.uniform(0.1, 0.3),
                'color': random.choice(STAR_COLORS)
            })
            
        self.clouds = []
        for _ in range(5):
            self.clouds.append({
                'x': random.randint(0, SCREEN_W),
                'y': random.randint(0, SCREEN_H//2),
                'width': random.randint(60, 120),
                'height': random.randint(20, 40),
                'speed': random.uniform(0.05, 0.15),
                'color': random.choice(CLOUD_COLORS)
            })
        
        # Кнопки меню
        center_x = SCREEN_W // 2
        self.menu_buttons = [
            Button(center_x - 75, 150, 150, 40, "ИГРАТЬ", self.start_game),
            Button(center_x - 75, 200, 150, 40, "ВЫХОД", sys.exit)
        ]
        
        self.game_buttons = [
            Button(SCREEN_W - 100, 10, 90, 30, "МЕНЮ", self.show_main_menu),
            Button(SCREEN_W - 100, 50, 90, 30, "ПАУЗА", self.toggle_pause)
        ]

    def start_game(self):
        self.show_menu = False
        self.reset()
        
    def show_main_menu(self):
        self.show_menu = True
        self.paused = False
        
    def toggle_pause(self):
        if not self.game_over:
            self.paused = not self.paused

    def reset(self):
        self.eggs.clear()
        self.particles.clear()
        self.score = 0
        self.misses = 0
        self.game_over = False
        self.paused = False
        self.spawn_timer = 0.0
        self.spawn_interval_ms = SPAWN_BASE_MS
        self.difficulty_meter = 0.0
        self.combo = 0
        self.combo_timer = 0
        self.wolf.set_position(POS_LEFT_BOTTOM)

    def add_particles(self, x, y, count=10, color=EGG_SHINE):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def difficulty_speed(self):
        k = min(1.0, self.score / 100.0)
        return SPEED_BASE + (SPEED_MAX - SPEED_BASE) * k

    def difficulty_spawn_ms(self):
        k = min(1.0, self.score / 120.0)
        return int(SPAWN_BASE_MS - (SPAWN_BASE_MS - SPAWN_MIN_MS) * k)

    def spawn_egg(self):
        chute_id = random.choice([POS_LEFT_TOP, POS_RIGHT_TOP, POS_LEFT_BOTTOM, POS_RIGHT_BOTTOM])
        speed = self.difficulty_speed()
        self.eggs.append(Egg(chute_id, self.chutes, speed))

    def handle_catch_or_miss(self, egg):
        if egg.dead or egg.caught:
            return
        if egg.t < 1.0:
            return

        if self.wolf.position == egg.chute_id:
            egg.caught = True
            self.score += 1
            self.combo += 1
            self.combo_timer = 2.0
            self.wolf.trigger_catch()
            
            # Эффекты при ловле
            catch_pos = self.chutes[egg.chute_id]["catch"]
            self.add_particles(catch_pos[0], catch_pos[1], 15, OK_COLOR)
            
        else:
            egg.dead = True
            self.misses += 1
            self.combo = 0
            miss_pos = self.chutes[egg.chute_id]["catch"]
            self.add_particles(miss_pos[0], miss_pos[1], 10, DANGER_COLOR)
            
            if self.misses >= MISS_TO_GAMEOVER:
                self.game_over = True
                self.add_particles(SCREEN_W//2, SCREEN_H//2, 30, DANGER_COLOR)

    def update_background(self, dt):
        # Обновление звезд
        for star in self.stars:
            star['x'] -= star['speed'] * dt * 10
            if star['x'] < 0:
                star['x'] = SCREEN_W
                star['y'] = random.randint(0, SCREEN_H)
        
        # Обновление облаков
        for cloud in self.clouds:
            cloud['x'] -= cloud['speed'] * dt * 10
            if cloud['x'] < -cloud['width']:
                cloud['x'] = SCREEN_W
                cloud['y'] = random.randint(0, SCREEN_H//2)

    def draw_background(self, surf):
        # Рисуем звезды
        for star in self.stars:
            pygame.draw.circle(surf, star['color'], (int(star['x']), int(star['y'])), star['size'])
        
        # Рисуем облака
        for cloud in self.clouds:
            pygame.draw.ellipse(surf, cloud['color'], 
                               (cloud['x'], cloud['y'], cloud['width'], cloud['height']))

    def draw_vignette(self, surf):
        # Создаем поверхность для виньетки
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        
        # Рисуем радиальный градиент
        for r in range(150, 0, -1):
            alpha = int(150 * (1 - r/150))
            pygame.draw.circle(vignette, (0, 0, 0, alpha), 
                              (SCREEN_W//2, SCREEN_H//2), r, 1)
        
        surf.blit(vignette, (0, 0))

    def process_input(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]
        
        if self.show_menu:
            for button in self.menu_buttons:
                button.update(mouse_pos, mouse_click)
        else:
            for button in self.game_buttons:
                button.update(mouse_pos, mouse_click)
                
            if not self.paused and not self.game_over:
                keys = pygame.key.get_pressed()
                left, right, up, down = keys[pygame.K_LEFT], keys[pygame.K_RIGHT], keys[pygame.K_UP], keys[pygame.K_DOWN]

                if left and up:
                    self.wolf.set_position(POS_LEFT_TOP)
                elif left and down:
                    self.wolf.set_position(POS_LEFT_BOTTOM)
                elif right and up:
                    self.wolf.set_position(POS_RIGHT_TOP)
                elif right and down:
                    self.wolf.set_position(POS_RIGHT_BOTTOM)

                if keys[pygame.K_q]:
                    self.wolf.set_position(POS_LEFT_TOP)
                if keys[pygame.K_a]:
                    self.wolf.set_position(POS_LEFT_BOTTOM)
                if keys[pygame.K_e]:
                    self.wolf.set_position(POS_RIGHT_TOP)
                if keys[pygame.K_d]:
                    self.wolf.set_position(POS_RIGHT_BOTTOM)

    def update(self, dt):
        if self.paused or self.game_over:
            return

        self.update_background(dt)
        self.wolf.update(dt)
        
        # Обновление комбо
        if self.combo_timer > 0:
            self.combo_timer -= dt
        
        # Спавн яиц
        self.spawn_timer += dt * 1000.0
        target_interval = self.difficulty_spawn_ms()
        if self.spawn_timer >= target_interval:
            self.spawn_timer = 0.0
            self.spawn_egg()

        # Движение яиц
        for egg in self.eggs:
            egg.update(dt)
            self.handle_catch_or_miss(egg)

        # Обновление частиц
        self.particles = [p for p in self.particles if p.update(dt)]

        # Чистка списка яиц
        self.eggs = [e for e in self.eggs if not e.dead and e.t < 1.0 or (e.caught and e.t <= 1.0)]

    def draw_chutes(self, surf):
        for chute in self.chutes.values():
            pts = chute["points"]
            for i in range(len(pts) - 1):
                pygame.draw.line(surf, LINE_COLOR, pts[i], pts[i + 1], 3)
                # Свечение желобов
                pygame.draw.line(surf, (*LINE_COLOR, 50), pts[i], pts[i + 1], 7)

    def draw_ui(self, surf):
        if self.show_menu:
            self.draw_menu(surf)
        else:
            self.draw_game_ui(surf)

    def draw_menu(self, surf):
        # Фон меню
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surf.blit(overlay, (0, 0))
        
        # Заголовок
        title = self.font_title.render("EGG CATCHER", True, TEXT_COLOR)
        shadow = self.font_title.render("EGG CATCHER", True, TEXT_SHADOW)
        surf.blit(shadow, (SCREEN_W//2 - title.get_width()//2 + 2, 62))
        surf.blit(title, (SCREEN_W//2 - title.get_width()//2, 60))
        
        subtitle = self.font.render("Nintendo Style", True, OK_COLOR)
        surf.blit(subtitle, (SCREEN_W//2 - subtitle.get_width()//2, 110))
        
        # Кнопки меню
        for button in self.menu_buttons:
            button.draw(surf, self.font)
            
        # Управление в подвале
        controls = [
            "Управление: Q/A/E/D или стрелки",
            "Пробел - пауза, R - рестарт",
            "Esc - выход"
        ]
        
        for i, text in enumerate(controls):
            text_surf = self.font_small.render(text, True, TEXT_COLOR)
            surf.blit(text_surf, (SCREEN_W//2 - text_surf.get_width()//2, 280 + i*25))

    def draw_game_ui(self, surf):
        # Панель счета
        score_bg = pygame.Rect(10, 10, 150, 60)
        pygame.draw.rect(surf, (0, 0, 0, 150), score_bg, border_radius=5)
        pygame.draw.rect(surf, UI_COLOR, score_bg, 2, border_radius=5)
        
        # Счет
        score_text = self.font.render(f"СЧЕТ: {self.score}", True, TEXT_COLOR)
        surf.blit(score_text, (20, 15))
        
        # Промахи
        hearts = "❤️ " * (MISS_TO_GAMEOVER - self.misses) + "💔 " * self.misses
        miss_text = self.font.render(hearts, True, TEXT_COLOR)
        surf.blit(miss_text, (20, 45))
        
        # Комбо
        if self.combo > 1 and self.combo_timer > 0:
            combo_color = lerp_color(OK_COLOR, (255, 200, 0), min(1.0, self.combo/10.0))
            combo_text = self.font_big.render(f"COMBO x{self.combo}!", True, combo_color)
            surf.blit(combo_text, (SCREEN_W//2 - combo_text.get_width()//2, 80))
        
        # Уровень сложности
        level = min(5, self.score // 20 + 1)
        level_text = self.font_small.render(f"Уровень: {level}", True, TEXT_COLOR)
        surf.blit(level_text, (SCREEN_W - 100, 90))
        
        # Кнопки игры
        for button in self.game_buttons:
            button.draw(surf, self.font_small)
        
        # Сообщения о паузе/game over
        if self.paused:
            s = self.font_big.render("ПАУЗА", True, TEXT_COLOR)
            surf.blit(s, (SCREEN_W//2 - s.get_width()//2, 150))
            hint = self.font.render("Пробел - продолжить", True, TEXT_COLOR)
            surf.blit(hint, (SCREEN_W//2 - hint.get_width()//2, 190))
            
        if self.game_over:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surf.blit(overlay, (0, 0))
            
            s1 = self.font_big.render("ИГРА ОКОНЧЕНА", True, DANGER_COLOR)
            s2 = self.font.render(f"Финальный счет: {self.score}", True, TEXT_COLOR)
            s3 = self.font.render("R - новая игра", True, TEXT_COLOR)
            
            surf.blit(s1, (SCREEN_W//2 - s1.get_width()//2, 120))
            surf.blit(s2, (SCREEN_W//2 - s2.get_width()//2, 170))
            surf.blit(s3, (SCREEN_W//2 - s3.get_width()//2, 210))

    def draw_particles(self, surf):
        for particle in self.particles:
            particle.draw(surf)

    def draw(self):
        # Фон с узором
        self.screen.fill(BACKGROUND_COLOR)
        
        # Анимированный фон
        self.draw_background(self.screen)
        
        # Сетчатый фон
        for x in range(0, SCREEN_W, 20):
            pygame.draw.line(self.screen, (40, 40, 50), (x, 0), (x, SCREEN_H), 1)
        for y in range(0, SCREEN_H, 20):
            pygame.draw.line(self.screen, (40, 40, 50), (0, y), (SCREEN_W, y), 1)
        
        # Игровые элементы
        self.draw_chutes(self.screen)
        self.wolf.draw(self.screen)
        
        for egg in self.eggs:
            egg.draw(self.screen)
            
        self.draw_particles(self.screen)
        self.draw_ui(self.screen)
        
        # Виньетка (затемнение по краям)
        self.draw_vignette(self.screen)
        
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS_BASE) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.show_menu:
                            pygame.quit()
                            sys.exit(0)
                        else:
                            self.show_menu = True
                    if event.key == pygame.K_SPACE and not self.show_menu:
                        self.toggle_pause()
                    if event.key == pygame.K_r and not self.show_menu:
                        self.reset()

            self.process_input()
            if not self.show_menu and not self.paused:
                self.update(dt)
            self.draw()

if __name__ == "__main__":
    Game().run()

