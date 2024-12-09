import random
from PyQt5.QtGui import QColor

FRAME_RATE = 60
LAMPPOST_RESTORE_TIME = 3500


class Bird:
    def __init__(self, x, y, sitting_time):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.radius = 10
        self.color = QColor(0, 0, 255)
        self.sitting_time = sitting_time
        self.time_sat = 0  # Время, которое птица уже просидела
        self.is_sitting = False
        self.current_lamppost = None
        self.speed = 1.3  # Скорость движения птицы
        self.flying_up = False  # Индикатор состояния полета вверх
        self.flying_up_time = 0  # Оставшееся время подъема

        self.t = 0  # Прогресс движения от 0 до 1
        self.total_time = None  # Общее время полета к столбу
        self.x0 = None  # Начальная позиция
        self.y0 = None  # Начальная позиция
        self.h = 50  # Высота параболы полета

    def start_flying_up(self):
        self.flying_up = True
        self.is_sitting = False
        self.flying_up_time = 10000 * random.random()
        self.x0 = self.x
        self.y0 = self.y
        self.target_x = self.x + random.randint(-200, 200)
        self.target_y = -100 + random.randint(-100, 150)
        dx = self.target_x - self.x0
        dy = self.target_y - self.y0
        distance = (dx**2 + dy**2)**0.5
        self.total_time = distance / (self.speed * FRAME_RATE)
        self.t = 0
        self.h = distance * 0.2  # Параметр для параболической траектории

    def update(self, delta_time, lampposts):
        if self.time_sat >= self.sitting_time:
            self.fly_away()
            return

        if self.flying_up:
            if self.t < 1:
                self.t += delta_time / self.total_time
                if self.t >= 1:
                    self.x = self.target_x
                    self.y = self.target_y
                    self.flying_up = False
                else:
                    t = self.t
                    self.x = self.x0 + (self.target_x - self.x0) * t
                    self.y = self.y0 + (self.target_y - self.y0) * \
                        t - self.h * 4 * t * (1 - t)
            else:
                self.flying_up = False
        elif self.is_sitting:
            self.time_sat += delta_time * 1000
            if self.current_lamppost and self.current_lamppost.status == 'fallen':
                if self in self.current_lamppost.current_birds:
                    self.current_lamppost.current_birds.remove(self)
                self.current_lamppost = None
                self.start_flying_up()
        else:
            if not self.current_lamppost:
                available_lampposts = [
                    lp for lp in lampposts if lp.status == 'standing']
                if available_lampposts:
                    self.current_lamppost = random.choice(available_lampposts)
                    self.target_x = self.current_lamppost.x + self.current_lamppost.width / 2
                    self.target_y = self.current_lamppost.y

                    self.x0 = self.x
                    self.y0 = self.y
                    dx = self.target_x - self.x0
                    dy = self.target_y - self.y0
                    distance = (dx**2 + dy**2)**0.5
                    self.total_time = distance / (self.speed * FRAME_RATE)
                    self.t = 0
                    self.h = distance * 0.2
            else:
                if self.t < 1:
                    if self.total_time != 0:
                        self.t += delta_time / self.total_time
                    else:
                        self.t += delta_time / (self.total_time+0.0001)
                    if self.t >= 1:
                        self.x = self.target_x
                        self.y = self.target_y
                        self.is_sitting = True
                        self.current_lamppost.current_birds.append(self)
                    else:
                        t = self.t
                        self.x = self.x0 + (self.target_x - self.x0) * t
                        self.y = self.y0 + \
                            (self.target_y - self.y0) * \
                            t - self.h * 4 * t * (1 - t)
                else:
                    self.x = self.target_x
                    self.y = self.target_y
                    self.is_sitting = True
                    self.current_lamppost.current_birds.append(self)

    def fly_away(self):
        if self.current_lamppost and self in self.current_lamppost.current_birds:
            self.current_lamppost.current_birds.remove(self)
        self.current_lamppost = None
        self.start_flying_up()


class LampPost:
    def __init__(self, x, y, max_birds):
        self.x = x
        self.y = y

        self.width = 10
        self.height = 150
        self.color = QColor(139, 69, 19)
        self.max_birds = max_birds
        self.current_birds = []
        self.status = 'standing'
        self.fall_time = 0

    def update(self, delta_time):
        if self.status == 'standing':
            if len(self.current_birds) > self.max_birds:
                self.status = 'fallen'
                self.fall_time = LAMPPOST_RESTORE_TIME
                for bird in self.current_birds:
                    bird.is_sitting = False
                    bird.current_lamppost = None
                self.current_birds.clear()
        else:
            self.fall_time -= delta_time * 1000
            if self.fall_time <= 0:
                self.status = 'standing'
                self.color = QColor(139, 69, 19)
