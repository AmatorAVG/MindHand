import math

from kivy.graphics import Color
from kivy.metrics import dp


def normalize_pressure(pressure):
    print(pressure)
    # this might mean we are on a device whose pressure value is
    # incorrectly reported by SDL2, like recent iOS devices.
    if pressure == 0.0:
        return 1
    return dp(pressure * 10)

def calculate_points(x1, y1, x2, y2, steps=5):
    dx = x2 - x1
    dy = y2 - y1
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < steps:
        return
    o = []
    m = dist / steps
    for i in range(1, int(m)):
        mi = i / m
        lastx = x1 + dx * mi
        lasty = y1 + dy * mi
        o.extend([lastx, lasty])
    return o

def kivy_color_to_svg(color: Color) -> str:
    r_hex = format(int(color.r * 255), "02x")
    g_hex = format(int(color.g * 255), "02x")
    b_hex = format(int(color.b * 255), "02x")
    a_hex = format(int(color.a * 255), "02x")
    return f"#{r_hex}{g_hex}{b_hex}{a_hex}"


def generate_points_on_line(points: list, point_size: int) -> list:
    """
    Генерирует список координат точек, расположенных на прямой,
    соединяющей две точки points, с заданным промежутком.

    Args:
      points: Список координат двух точек [x1, y1, x2, y2].
      point_size: Размер точки в пикселях.

    Returns:
      Список координат точек на прямой.
    """
    # points = [0, 0, 50, 50, 100, 200]
    if len(points) == 2:
        return points
    generated_points = []
    for i in range(0, len(points) - 2, 2):
        x1, y1, x2, y2 = points[i], points[i + 1], points[i + 2], points[i + 3]

        # Вычисление длины прямой
        line_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        # Количество точек на прямой
        num_points = max(int(line_length / (point_size / 7)) + 1, 2)

        # Создание списка координат точек
        for i in range(num_points):
            # Вычисление координат точки на прямой
            x = round(x1 + (x2 - x1) * i / (num_points - 1))
            y = round(y1 + (y2 - y1) * i / (num_points - 1))
            if not (generated_points and generated_points[-2:] == [x, y]):
                generated_points.extend([x, y])

    return generated_points
