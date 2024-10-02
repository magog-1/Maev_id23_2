import sys
import math
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QColor


class DrawingArea(QWidget):
    def __init__(self):
        super().__init__()
        self.radius = 200          # Радиус окружности
        self.angle = 0             # угол
        self.point_radius = 10      # Радиус точки
        self.speed = 10        # 2 часть задания
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_angle)
        self.timer.start(50)        # Обновление угла каждую 50 миллисекунд

    def update_angle(self):
        self.angle += self.speed              # Увеличиваем угол в зависимости от скорости
        if self.angle >= 360:
            self.angle -= 360          
        elif self.angle < 0:
            self.angle += 360          
        self.update()                 # Перерисовка

    def paintEvent(self, event):
        painter = QPainter(self)

        # Центр области рисования
        center_x = self.width() // 2
        center_y = self.height() // 2

        # окружность
        painter.setPen(QColor(255, 255, 255))  # белый цвет окружности
        painter.drawEllipse(center_x - self.radius, center_y -
                            self.radius, self.radius * 2, self.radius * 2)

        # положение движущейся точки
        point_x = center_x + self.radius * math.cos(math.radians(self.angle))
        point_y = center_y + self.radius * math.sin(math.radians(self.angle))

        # точка
        painter.setBrush(QColor(255, 0, 0))  # Красный цвет точки
        painter.drawEllipse(int(point_x - self.point_radius), int(point_y -
                            self.point_radius), int(self.point_radius * 2), int(self.point_radius * 2))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Движущаяся точка по окружности") 
        self.setFixedSize(600, 600)  # размеры

        self.drawing_area = DrawingArea()
        # Устанавливаем область рисования как центральный виджет
        self.setCentralWidget(self.drawing_area)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()  
    sys.exit(app.exec())  
