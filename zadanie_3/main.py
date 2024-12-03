import sys
import random
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget, QSlider, QVBoxLayout, QLabel, QSpinBox, QHBoxLayout, QPushButton, QDialog, QFormLayout, QGridLayout
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from models import Bird, LampPost

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
NUM_BIRDS = 11
NUM_LAMPPOSTS = 6
FRAME_RATE = 60


class SimulationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Птицы и столбы')
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Инициализация состояния
        self.birds = []
        self.lampposts = []
        self.paused = False  # пауза

        self.init_ui()

        # Загрузка начального состояния из файла
        self.load_initial_state()

        # Таймер
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(1000 // FRAME_RATE)  # 60 FPS

        self.bird_spawn_timer = 0
        self.lamppost_spawn_timer = 0
        self.bird_spawn_interval = 9999999999
        self.lamppost_spawn_interval = 9999999999

        self.last_time = 0

    def init_ui(self):
        # Слайдер для частоты появления птиц
        self.bird_frequency_slider = QSlider(Qt.Horizontal, self)
        self.bird_frequency_slider.setRange(0, 100)
        self.bird_frequency_slider.setValue(0)
        self.bird_frequency_slider.valueChanged.connect(
            self.update_bird_frequency)
        self.bird_frequency_slider.setGeometry(20, 20, 200, 20)

        self.bird_frequency_label = QLabel("Частота появления птиц", self)
        self.bird_frequency_label.move(20, 0)

        # Слайдер для частоты появления столбов
        self.lamppost_frequency_slider = QSlider(Qt.Horizontal, self)
        self.lamppost_frequency_slider.setRange(0, 100)
        self.lamppost_frequency_slider.setValue(0)
        self.lamppost_frequency_slider.valueChanged.connect(
            self.update_lamppost_frequency)
        self.lamppost_frequency_slider.setGeometry(20, 60, 200, 20)

        self.lamppost_frequency_label = QLabel(
            "Частота появления столбов", self)
        self.lamppost_frequency_label.move(20, 40)

        # Кнопка для паузы
        self.pause_button = QPushButton("Пауза", self)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setGeometry(20, 100, 200, 30)

    def toggle_pause(self):
        if self.paused:
            self.timer.start(1000 // FRAME_RATE)
            self.pause_button.setText("Пауза")
        else:
            self.timer.stop()
            self.pause_button.setText("Возобновить")
        self.paused = not self.paused

    def update_bird_frequency(self):
        slider_value = self.bird_frequency_slider.value()
        self.bird_spawn_interval = max(1000, 10000 - slider_value * 90)

    def update_lamppost_frequency(self):
        slider_value = self.lamppost_frequency_slider.value()
        self.lamppost_spawn_interval = max(1000, 10000 - slider_value * 90)

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
        if self.paused:
            return

        delta_time = 1 / FRAME_RATE
        self.bird_spawn_timer += delta_time * 1000
        self.lamppost_spawn_timer += delta_time * 1000

        # Появление новых птиц
        if self.bird_spawn_timer >= self.bird_spawn_interval:
            self.spawn_new_bird()
            self.bird_spawn_timer = 0

        # Появление новых столбов
        if self.lamppost_spawn_timer >= self.lamppost_spawn_interval:
            self.spawn_new_lamppost()
            self.lamppost_spawn_timer = 0

        birds_to_remove = []
        for bird in self.birds:
            bird.update(delta_time, self.lampposts)

            if bird.flying_up and (bird.y < -50 or bird.y > WINDOW_HEIGHT + 50 or bird.x < -50 or bird.x > WINDOW_WIDTH + 50):
                birds_to_remove.append(bird)

        for bird in birds_to_remove:
            self.birds.remove(bird)

        # Обновление столбов
        for lp in self.lampposts:
            lp.update(delta_time)

        self.repaint()

    def spawn_new_bird(self):
        x = random.randint(50, WINDOW_WIDTH - 50)
        y = random.randint(10, 40)
        sitting_time = 100000
        bird = Bird(x, y, sitting_time)
        self.birds.append(bird)

    def spawn_new_lamppost(self):
        x = random.randint(50, WINDOW_WIDTH - 50)
        y = random.randint(300, 380)
        max_birds = 2
        lamppost = LampPost(x, y, max_birds)
        self.lampposts.append(lamppost)

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

                painter.setPen(QPen(Qt.darkGray))
                painter.drawLine(lp.x, lp.y + lp.height, lp.x + lp.width, lp.y)

        for bird in self.birds:
            painter.setBrush(QBrush(bird.color))
            painter.setPen(QPen(Qt.black))
            painter.drawEllipse(QPointF(bird.x, bird.y),
                                bird.radius, bird.radius)

    def closeEvent(self, event):
        self.save_initial_state()
        event.accept()

    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        clicked_lamppost = None
        for lp in self.lampposts:
            if lp.x <= x <= lp.x + lp.width and lp.y <= y <= lp.y + lp.height:
                clicked_lamppost = lp
                break
        if clicked_lamppost:
            # Редактирование существующего столба
            dialog = LamppostDialog(clicked_lamppost)
            dialog.exec_()
        else:
            # Создание нового столба
            dialog = LamppostDialog()
            if dialog.exec_():
                new_lp = LampPost(x - 5, y, dialog.max_birds_spinbox.value())
                self.lampposts.append(new_lp)


class LamppostDialog(QDialog):
    def __init__(self, lamppost=None):
        super().__init__()
        self.setWindowTitle("Настройки столба")
        self.lamppost = lamppost
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()
        self.max_birds_spinbox = QSpinBox()
        self.max_birds_spinbox.setRange(1, 10)
        if self.lamppost:
            self.max_birds_spinbox.setValue(self.lamppost.max_birds)
        else:
            self.max_birds_spinbox.setValue(2)
        layout.addRow("Прочность столба (макс. птиц):", self.max_birds_spinbox)
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addRow(buttons_layout)
        self.setLayout(layout)

    def accept(self):
        if self.lamppost:
            self.lamppost.max_birds = self.max_birds_spinbox.value()
        super().accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimulationWindow()
    window.show()
    sys.exit(app.exec_())
