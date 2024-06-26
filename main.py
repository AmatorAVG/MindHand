"""
Touch Tracer Line Drawing Demonstration
=======================================

This demonstrates tracking each touch registered to a device. You should
see a basic background image. When you press and hold the mouse, you
should see cross-hairs with the coordinates written next to them. As
you drag, it leaves a trail. Additional information, like pressure,
will be shown if they are in your device's touch.profile.

.. note::

   A function `calculate_points` handling the points which will be drawn
   has by default implemented a delay of 5 steps. To get more precise visual
   results lower the value of the optional keyword argument `steps`.

This program specifies an icon, the file icon.png, in its App subclass.
It also uses the particle.png file as the source for drawing the trails which
are white on transparent. The file touchtracer.kv describes the application.

The file android.txt is used to package the application for use with the
Kivy Launcher Android application. For Android devices, you can
copy/paste this directory into /sdcard/kivy/touchtracer on your Android device.

"""

__version__ = "1.0"

from enum import Enum
from xml.dom import minidom

import kivy
from kivy.core.window import Window
from kivy.graphics.context_instructions import Scale, PushMatrix, PopMatrix
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from schemas import PointSchema, LineSchema
from services import (
    generate_points_on_line,
    kivy_color_to_svg,
    calculate_points,
    normalize_pressure,
)

kivy.require("1.0.6")

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Point, GraphicException
from kivy.metrics import dp
from random import random


# # SOURCE = "particle.png"
# SOURCE = "egg_circle.png"
# # SOURCE = None
# # POINTSIZE = 30


class Pens(Enum):
    PEN = ("Ручка", "egg_circle.png")
    PENCIL = ("Карандаш", "particle.png")
    ERASER = ("Ластик", "egg_circle.png")

# LineSchema.model_rebuild()
class Touchtracer(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.curve_count = 0
        self.curve_points: dict[int, LineSchema] = {}
        self.current_pen = Pens.PEN
        self.current_pen_size = 10

        # Переменные для масштабирования
        self.scale = 1
        self.scale_factor = 1.1
        self.mouse_down_pos = None
        self.last_x, self.last_y = 0, 0

    def on_touch_down(self, touch):
        # return
        # Запоминаем позицию нажатия правой кнопки
        print(touch.button)
        if touch.button == 'right':
            self.mouse_down_pos = touch.pos
            self.last_x, self.last_y = touch.x, touch.y  # Запоминаем позицию для рисования
            return
        # Начинаем рисовать линию при нажатии левой кнопкой
        win = self.get_parent_window()
        ud = touch.ud
        ud["group"] = g = str(touch.uid)
        pointsize = self.current_pen_size
        if "pressure" in touch.profile:
            ud["pressure"] = touch.pressure
            pointsize = normalize_pressure(touch.pressure)
        # ud["color"] = random()

        with self.canvas:
            ud["color"] = (
                Color(0, 0, 0, 1, group=g)
                if self.current_pen == Pens.ERASER
                else Color(random(), random(), random(), 1, group=g)
            )
            ud["lines"] = [
                # Rectangle(pos=(touch.x, 0), size=(1, win.height), group=g),
                # Rectangle(pos=(0, touch.y), size=(win.width, 1), group=g),
                Point(
                    points=(touch.x, touch.y),
                    source=self.current_pen.value[1],
                    pointsize=round(pointsize * self.scale),
                    group=g,
                )
            ]

        ud["label"] = Label(size_hint=(None, None))
        self.update_touch_label(ud["label"], touch)
        self.add_widget(ud["label"])
        touch.grab(self)
        self.curve_count += 1
        self.curve_points[self.curve_count] = LineSchema(
            x=int(round(touch.x / self.scale)),
            y=int(round(touch.y / self.scale)),
            size=pointsize,
            color=kivy_color_to_svg(ud["color"]),
            pen=self.current_pen.name
        )

        return True

    def on_touch_move(self, touch):
        # Масштабирование при зажатой правой кнопке
        if touch.button == 'right' and self.mouse_down_pos:
            dx = touch.x - self.mouse_down_pos[0]
            dy = touch.y - self.mouse_down_pos[1]

            # Изменяем масштаб
            if abs(dx) > 5 or abs(dy) > 5:
                if dx > 0:
                    self.scale *= self.scale_factor
                elif dx < 0:
                    self.scale /= self.scale_factor

                self.scale = min(max(0.2, self.scale), 5)
                # Обновляем позицию нажатия
                self.mouse_down_pos = touch.x, touch.y

                # Применяем масштаб к канвасу
                self.canvas.clear() # Очищаем канвас перед обновлением
                with self.canvas:
                    PushMatrix()  # Сохраняем текущую матрицу преобразования
                    # self.canvas.translate = (touch.x, touch.y) # Переводим в точку касания
                    # self.canvas.scale = self.scale # Масштабируем
                    # Рисуем заново
                    print(self.scale)
                    Scale(self.scale, self.scale, self.scale)
                    # Color(1, 0, 0, 1)
                    # self.line = Line(points=(100, 100, 200, 200), width=2)
                    self.restore_canvas()
                    PopMatrix()  # Восстанавливаем матрицу преобразования
            return

        if touch.grab_current is not self:
            return
        ud = touch.ud
        # ud['lines'][0].pos = touch.x, 0
        # ud['lines'][1].pos = 0, touch.y

        index = -1

        while True:
            try:
                points = ud["lines"][index].points
                oldx, oldy = points[-2], points[-1]
                break
            except IndexError:
                index -= 1

        pointsize = (
            normalize_pressure(touch.pressure)
            if "pressure" in ud
            else round(self.current_pen_size * self.scale)
        )
        points = calculate_points(
            oldx, oldy, touch.x, touch.y, steps=pointsize / 7
        )

        # if pressure changed create a new point instruction
        if "pressure" in ud:
            old_pressure = ud["pressure"]
            if (
                not old_pressure
                or not 0.99 < (touch.pressure / old_pressure) < 1.01
            ):
                g = ud["group"]
                # pointsize = normalize_pressure(touch.pressure)
                with self.canvas:
                    # Color(ud["color"], 1, 1, mode="hsv", group=g)
                    # TODO реализовать цвет для ластика
                    Color(random(), random(), random(), 1, group=g)
                    ud["lines"].append(
                        Point(
                            points=(),
                            source=self.current_pen.value[1],
                            pointsize=pointsize,
                            group=g,
                        )
                    )

        if points:
            try:
                lp = ud["lines"][-1].add_point
                for idx in range(0, len(points), 2):
                    lp(points[idx], points[idx + 1])
                    # print(points[idx], 600-points[idx + 1])
                    self.curve_points[self.curve_count].points.append(
                        PointSchema(
                            x=int(round(points[idx] / self.scale)),
                            y=int(round(points[idx + 1] / self.scale)),
                            size=pointsize,
                        )
                    )
            except GraphicException:
                pass

        ud["label"].pos = touch.pos
        import time

        t = int(time.time())
        if t not in ud:
            ud[t] = 1
        else:
            ud[t] += 1
        # self.update_touch_label(ud["label"], touch)

    def on_touch_up(self, touch):
        return
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        ud = touch.ud
        self.canvas.remove_group(ud["group"])
        self.remove_widget(ud["label"])

    def update_touch_label(self, label, touch):
        return
        label.text = "ID: %s\nPos: (%d, %d)\nClass: %s" % (
            touch.id,
            touch.x,
            touch.y,
            touch.__class__.__name__,
        )
        label.texture_update()
        label.pos = touch.pos
        label.size = label.texture_size[0] + 20, label.texture_size[1] + 20

    def save_to_svg(self):
        filename = "drawing.svg"
        with open(filename, "w") as f:
            f.write(
                '<svg xmlns="http://www.w3.org/2000/svg" height="{0}" '
                'width="{1}">\n'.format(dp(800), dp(600))
            )
            for curve in self.curve_points.values():
                f.write(
                    '<path d="M{0} {1} '.format(
                        int(curve.x), int(dp(600) - curve.y)
                    )
                )
                for point in curve.points:
                    f.write(
                        "L{0} {1} ".format(point.x, int(dp(600) - point.y))
                    )
                f.write(
                    f'" fill="none" stroke="{curve.color}" stroke-width="'
                    f'{curve.size}" pen="{curve.pen}"/>\n'
                )
            f.write("</svg>")
        print("Saved as", filename)

    def clear_canvas(self):
        self.canvas.clear()
        self.curve_count = 0
        self.curve_points = {}

    def parse_svg(self, svg_filename: str):
        """Отображаем ранее сохраненный SVG-файл на канве"""
        svg_dom = minidom.parse(svg_filename)
        path_strings = [
            (
                path.getAttribute("d"),
                path.getAttribute("stroke"),
                path.getAttribute("stroke-width"),
                path.getAttribute("pen"),
            )
            for path in svg_dom.getElementsByTagName("path")
        ]

        for path_string in path_strings:
            self.curve_count += 1
            with self.canvas:
                Color(*get_color_from_hex(path_string[1]))
                points_svg = path_string[0].split()
                points = []
                for i in range(0, len(points_svg), 2):
                    x = int(points_svg[i][1:])
                    y = int(points_svg[i + 1])
                    points.extend([x, int(dp(600) - y)])
                pointsize = int(path_string[2])
                points_on_line = generate_points_on_line(points, pointsize)
                Point(
                    points=points_on_line, source=Pens[path_string[
                        3]].value[1],
                    pointsize=pointsize
                )

                self.curve_points[self.curve_count] = LineSchema(
                    x=points_on_line[0],
                    y=points_on_line[1],
                    size=pointsize,
                    color=path_string[1],
                    pen=path_string[3],
                )
                for i in range(2, len(points_on_line), 2):
                    self.curve_points[self.curve_count].points.append(
                        PointSchema(
                            x=points_on_line[i],
                            y=points_on_line[i + 1],
                            size=pointsize,
                        )
                    )
                # g = str(self.curve_count)
                # ud["lines"] = [
                # Rectangle(pos=(touch.x, 0), size=(1, win.height), group=g),
                # Rectangle(pos=(0, touch.y), size=(win.width, 1), group=g),

                # ]
    def restore_canvas(self):
        for line in self.curve_points.values():
            Color(*get_color_from_hex(line.color))
            line_points = [line.x, line.y]
            for point in line.points:
                line_points.append(point.x)
                line_points.append(point.y)
            p = [line.x, line.y].extend([coord for point in line.points for
                                         coord in [point.x, point.y]])
            Point(points=line_points, source=Pens[
                    line.pen].value[1],
                pointsize=line.size
            )

class TouchtracerApp(App):
    title = "Touchtracer"
    icon = "icon.png"

    def checkbox_pen_pressed(self, instance):
        self.painter.current_pen = Pens.PEN

    def checkbox_pencil_pressed(self, instance):
        self.painter.current_pen = Pens.PENCIL

    def checkbox_eraser_pressed(self, instance):
        self.painter.current_pen = Pens.ERASER

    def slider_pen_size_move(self, instance, value):
        self.painter.current_pen_size = value

    def build(self):

        parent = Widget()
        self.painter = Touchtracer()

        savebtn = Button(text="Save", pos=(10, 20), size=(100, 30))
        savebtn.bind(on_release=self.save_canvas)

        clearbtn = Button(text="Clear", pos=(120, 20), size=(100, 30))
        clearbtn.bind(on_release=self.clear_canvas)

        openbtn = Button(text="Open", pos=(230, 20), size=(100, 30))
        openbtn.bind(on_release=self.open_svg)

        parent.add_widget(self.painter)
        parent.add_widget(clearbtn)
        parent.add_widget(savebtn)
        parent.add_widget(openbtn)

        parent.add_widget(Label(text=Pens.PEN.value[0], pos=(350, -20)))
        parent.add_widget(
            CheckBox(
                group="pens",
                pos=(350, 10),
                color=[1, 1, 1],
                active=True,
                allow_no_selection=False,
                on_press=self.checkbox_pen_pressed,
            )
        )
        parent.add_widget(Label(text=Pens.PENCIL.value[0], pos=(450, -20)))
        parent.add_widget(
            CheckBox(
                group="pens",
                pos=(450, 10),
                color=[1, 1, 1],
                allow_no_selection=False,
                on_press=self.checkbox_pencil_pressed,
            )
        )
        parent.add_widget(Label(text=Pens.ERASER.value[0], pos=(550, -20)))
        parent.add_widget(
            CheckBox(
                group="pens",
                pos=(550, 10),
                color=[1, 1, 1],
                allow_no_selection=False,
                on_press=self.checkbox_eraser_pressed,
            )
        )

        slider = Slider(orientation='vertical', min=1, max=30,
                                 value=10, pos=(650, 10), size=(100, 130),
                        step=1,
                                 # on_touch_move=self.slider_pen_size_move
                        )
        parent.add_widget(slider)
        slider.bind(value=self.slider_pen_size_move)
        print("Canvas size:", Window.size)

        return parent

    def open_svg(self, instance):
        with self.painter.canvas:
            # Очистить канву перед отображением нового SVG файла
            self.painter.clear_canvas()
            self.painter.scale = 1
            self.painter.parse_svg("drawing.svg")

    def clear_canvas(self, obj):
        self.painter.clear_canvas()

    def save_canvas(self, obj):
        self.painter.save_to_svg()

    def on_pause(self):
        return True


if __name__ == "__main__":
    TouchtracerApp().run()
