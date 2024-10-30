import sys
import random
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
NUM_BIRDS = 11
NUM_LAMPPOSTS = 6
FRAME_RATE = 60
LAMPPOST_RESTORE_TIME = 5000


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
        self.speed = 0.7  # Скорость движения птицы
        self.flying_up = False  # Индикатор состояния полета вверх
        self.flying_up_time = 0  # Оставшееся время подъема

    def update(self, delta_time, lampposts):
        if self.time_sat >= self.sitting_time:
            self.fly_away()
            return

        if self.flying_up:
            # Птица летит вверх
            self.y -= self.speed
            # Уменьшаем оставшееся время подъема
            self.flying_up_time -= delta_time * 1000
            if self.flying_up_time <= 0:
                self.flying_up = False
                # Птица начинает искать новый столб после подъема
                self.current_lamppost = None
        elif self.is_sitting:
            self.time_sat += delta_time * 1000  # Увеличиваем время сидения
            # Проверяем, не упал ли столб
            if self.current_lamppost and self.current_lamppost.status == 'fallen':
                # Столб упал, птица начинает подъем
                self.is_sitting = False
                self.current_lamppost = None
                self.flying_up = True
                self.flying_up_time = 2000  # Птица поднимается вверх в течение 2 секунд
        else:
            # Ищем столб для посадки, если птица не сидит и не летит вверх
            if not self.current_lamppost:
                available_lampposts = [
                    lp for lp in lampposts if lp.status == 'standing']
                if available_lampposts:
                    self.current_lamppost = random.choice(available_lampposts)
                    self.target_x = self.current_lamppost.x + self.current_lamppost.width/2
                    self.target_y = self.current_lamppost.y
            else:
                # Движение к столбу
                dx = self.target_x - self.x
                dy = self.target_y - self.y
                distance = (dx**2 + dy**2)**0.5
                if distance > self.speed:
                    self.x += dx / distance * self.speed
                    self.y += dy / distance * self.speed
                else:
                    # Прибыли на столб
                    self.x = self.target_x
                    self.y = self.target_y
                    self.is_sitting = True
                    self.current_lamppost.current_birds.append(self)

    def fly_away(self):
        # Удаляем птицу из списка птиц на столбе
        if self.current_lamppost and self in self.current_lamppost.current_birds:
            self.current_lamppost.current_birds.remove(self)

        # Птица улетает за пределы экрана
        self.x = -100
        self.y = -100
        self.is_sitting = False
        self.current_lamppost = None


class LampPost:
    def __init__(self, x, y, max_birds):
        self.x = x
        self.y = y

        self.width = 10
        self.height = 150
        self.color = QColor(139, 69, 19)
        self.max_birds = max_birds  
        self.current_birds = []
        self.status = 'standing'  # 'standing' или 'fallen'
        self.fall_time = 0  # Время, оставшееся до восстановления

    def update(self, delta_time):
        if self.status == 'standing':
            if len(self.current_birds) > self.max_birds:
                # Столб падает
                self.status = 'fallen'
                self.fall_time = LAMPPOST_RESTORE_TIME
                # Все птицы на этом столбе начинают искать новый столб
                for bird in self.current_birds:
                    bird.is_sitting = False
                    bird.current_lamppost = None
                self.current_birds.clear()
        else:
            self.fall_time -= delta_time * 1000
            if self.fall_time <= 0:
                # Столб восстанавливается
                self.status = 'standing'
                self.color = QColor(139, 69, 19)  # Коричневый цвет


class SimulationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Птицы и столбы')
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Инициализация состояния
        self.birds = []
        self.lampposts = []

        # Загрузка начального состояния из файла
        self.load_initial_state()

        # Таймер для управления обновлением
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(1000 // FRAME_RATE)  # 60 FPS

        self.last_time = 0

    def load_initial_state(self):
        if os.path.exists('initial_state.json'):
            try:
                with open('initial_state.json', 'r') as f:
                    data = json.load(f)
                    if 'lampposts' in data and 'birds' in data:
                        # Загрузка столбов
                        for lp_data in data['lampposts']:
                            lamppost = LampPost(
                                lp_data['x'], lp_data['y'], lp_data['max_birds'])
                            self.lampposts.append(lamppost)
                        # Загрузка птиц
                        for bird_data in data['birds']:
                            bird = Bird(
                                bird_data['x'], bird_data['y'], bird_data['sitting_time'])
                            self.birds.append(bird)
                    else:
                        # Если структура данных некорректна, создаём состояние по умолчанию
                        self.create_default_state()
            except (json.JSONDecodeError, KeyError):
                # Если произошла ошибка при чтении файла, создаём состояние по умолчанию
                self.create_default_state()
        else:
            # Создание начального состояния по умолчанию
            self.create_default_state()

    def create_default_state(self):
        # Создание столбов
        for _ in range(NUM_LAMPPOSTS):
            x = random.randint(50, WINDOW_WIDTH - 50)
            y = random.randint(300, 380)
            max_birds = 2
            lamppost = LampPost(x, y, max_birds)
            self.lampposts.append(lamppost)

        # Создание птиц
        for _ in range(NUM_BIRDS):
            x = random.randint(50, WINDOW_WIDTH - 50)
            y = random.randint(50, 150)
            sitting_time = 100000
            bird = Bird(x, y, sitting_time)
            self.birds.append(bird)

        # Сохранение начального состояния в файл
        self.save_initial_state()

    def save_initial_state(self):
        data = {'lampposts': [], 'birds': []}
        for lp in self.lampposts:
            data['lampposts'].append({
                'x': lp.x,
                'y': lp.y,
                'max_birds': lp.max_birds
            })
        for bird in self.birds:
            data['birds'].append({
                'x': bird.x,
                'y': bird.y,

                'sitting_time': bird.sitting_time
            })
        with open('initial_state.json', 'w') as f:
            json.dump(data, f)

    def update_simulation(self):
        delta_time = 1 / FRAME_RATE  # Время, прошедшее с предыдущего кадра
        # Обновление птиц
        for bird in self.birds:
            bird.update(delta_time, self.lampposts)
        # Обновление столбов
        for lp in self.lampposts:
            lp.update(delta_time)
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Рисование столбов
        for lp in self.lampposts:
            if lp.status == 'standing':
                painter.setBrush(QBrush(lp.color))
                painter.setPen(QPen(Qt.black))
                rect = QRectF(lp.x, lp.y, lp.width, lp.height)
                rect2 = QRectF(lp.x - 10, lp.y, 30, 10)
                painter.drawRect(rect)
                painter.drawRect(rect2)
            else:
                # Рисуем падение столба
                painter.setPen(QPen(Qt.darkGray))
                painter.drawLine(lp.x, lp.y + lp.height, lp.x + lp.width, lp.y)

        # Рисование птиц
        for bird in self.birds:
            painter.setBrush(QBrush(bird.color))
            painter.setPen(QPen(Qt.black))
            painter.drawEllipse(QPointF(bird.x, bird.y),
                                bird.radius, bird.radius)

    def closeEvent(self, event):
        # При закрытии окна сохраняем состояние
        self.save_initial_state()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimulationWindow()
    window.show()
    sys.exit(app.exec_())
