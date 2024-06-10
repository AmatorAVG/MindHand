import math


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
