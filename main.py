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

from xml.dom import minidom

import kivy
from kivy.core.window import Window
from kivy.graphics.svg import Svg
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from schemas import PointSchema, LineSchema

kivy.require("1.0.6")

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Point, GraphicException, Line
from kivy.metrics import dp
from random import random
from math import sqrt


def calculate_points(x1, y1, x2, y2, steps=5):
    dx = x2 - x1
    dy = y2 - y1
    dist = sqrt(dx * dx + dy * dy)
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
    # r, g, b, a = kivy_color
    r_hex = format(int(color.r * 255), "02x")
    g_hex = format(int(color.g * 255), "02x")
    b_hex = format(int(color.b * 255), "02x")
    a_hex = format(int(color.a * 255), "02x")
    return f"#{r_hex}{g_hex}{b_hex}{a_hex}"


class Touchtracer(FloatLayout):
    curve_count = 0
    curve_points: dict[int, LineSchema] = {}

    def normalize_pressure(self, pressure):
        print(pressure)
        # this might mean we are on a device whose pressure value is
        # incorrectly reported by SDL2, like recent iOS devices.
        if pressure == 0.0:
            return 1
        return dp(pressure * 10)

    def on_touch_down(self, touch):
        # return
        win = self.get_parent_window()
        ud = touch.ud
        ud["group"] = g = str(touch.uid)
        pointsize = 5
        print(touch.profile)
        if "pressure" in touch.profile:
            ud["pressure"] = touch.pressure
            pointsize = self.normalize_pressure(touch.pressure)
        # ud["color"] = random()

        with self.canvas:
            ud["color"] = Color(random(), random(), random(), 1, group=g)
            ud["lines"] = [
                # Rectangle(pos=(touch.x, 0), size=(1, win.height), group=g),
                # Rectangle(pos=(0, touch.y), size=(win.width, 1), group=g),
                Point(
                    points=(touch.x, touch.y),
                    # source="particle.png",
                    pointsize=pointsize,
                    group=g,
                )
            ]

        ud["label"] = Label(size_hint=(None, None))
        self.update_touch_label(ud["label"], touch)
        self.add_widget(ud["label"])
        touch.grab(self)
        self.curve_count += 1
        self.curve_points[self.curve_count] = LineSchema(
            x=int(round(touch.x)),
            y=int(round(touch.y)),
            size=pointsize,
            color=kivy_color_to_svg(ud["color"]),
        )

        return True

    def on_touch_move(self, touch):
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

        points = calculate_points(oldx, oldy, touch.x, touch.y)

        # if pressure changed create a new point instruction
        if "pressure" in ud:
            old_pressure = ud["pressure"]
            if (
                not old_pressure
                or not 0.99 < (touch.pressure / old_pressure) < 1.01
            ):
                g = ud["group"]
                pointsize = self.normalize_pressure(touch.pressure)
                with self.canvas:
                    # Color(ud["color"], 1, 1, mode="hsv", group=g)
                    Color(random(), random(), random(), 1, group=g)
                    ud["lines"].append(
                        Point(
                            points=(),
                            # source="particle.png",
                            pointsize=pointsize,
                            group=g,
                        )
                    )

        if points:
            try:
                lp = ud["lines"][-1].add_point
                for idx in range(0, len(points), 2):
                    lp(points[idx], points[idx + 1])
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
        self.curve_points[self.curve_count].points.append(
            PointSchema(
                x=int(round(touch.x)),
                y=int(round(touch.y)),
                size=(
                    self.normalize_pressure(touch.pressure)
                    if "pressure" in ud
                    else 1
                ),
            )
        )

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
                    f'" fill="none" stroke="{curve.color}" stroke-width="{curve.size}"/>\n'
                )
            f.write("</svg>")
        print("Saved as", filename)

    def clear_canvas(self):
        self.canvas.clear()
        self.curve_count = 0
        self.curve_points = {}

    def parse_svg(self, svg_filename):
        svg_dom = minidom.parse(svg_filename)
        path_strings = [
            (
                path.getAttribute("d"),
                path.getAttribute("stroke"),
                path.getAttribute("stroke-width"),
            )
            for path in svg_dom.getElementsByTagName("path")
        ]

        for path_string in path_strings:
            with self.canvas:
                Color(*get_color_from_hex(path_string[1]))
                points_svg = path_string[0].split()
                points = []
                for i in range(0, len(points_svg), 2):
                    x = int(points_svg[i][1:])
                    y = int(points_svg[i + 1])
                    points.extend([x, int(dp(600) - y)])
                    # Point(pointsize=int(path_string[2])).add_point(x, int(dp(600) - y))
                if len(points) == 2:
                    Point(
                        points=points,
                        # source="particle.png",
                        pointsize=int(path_string[2]),
                        # group=g,
                    )
                else:
                    Line(bezier=points, width=int(path_string[2]),
                         bezier_precision=50)

                # ud["lines"] = [
                # Rectangle(pos=(touch.x, 0), size=(1, win.height), group=g),
                # Rectangle(pos=(0, touch.y), size=(win.width, 1), group=g),

                # ]


# class SvgWidget(Scatter):
#
#     def __init__(self, filename, **kwargs):
#         super(SvgWidget, self).__init__(**kwargs)
#         with self.canvas:
#             svg = Svg(filename)
#         self.size = svg.width, svg.height


class TouchtracerApp(App):
    title = "Touchtracer"
    icon = "icon.png"

    def build(self):

        parent = Widget()
        self.painter = Touchtracer()

        savebtn = Button(text="Save", pos=(10, 20), size=(100, 50))
        savebtn.bind(on_release=self.save_canvas)

        clearbtn = Button(text="Clear", pos=(120, 20), size=(100, 50))
        clearbtn.bind(on_release=self.clear_canvas)

        openbtn = Button(text="Open", pos=(230, 20), size=(100, 50))
        openbtn.bind(on_release=self.open_svg)

        # self.image = Image()
        # self.image.size_hint = (0.5, 0.5)
        # self.image.pos_hint = {'x': 0.25, 'y': 0.35}
        #
        # self.painter.add_widget(self.image)

        parent.add_widget(self.painter)
        parent.add_widget(clearbtn)
        parent.add_widget(savebtn)
        parent.add_widget(openbtn)

        print("Canvas size:", Window.size)

        return parent

    def open_svg(self, instance):
        with self.painter.canvas:
            # Очистить канву перед отображением нового SVG файла
            self.painter.clear_canvas()
            self.painter.parse_svg("drawing.svg")
            # Открыть и отобразить SVG файл
            # svg = SvgWidget('drawing.svg', size_hint=(None, None))
            # self.painter.add_widget(svg)
            # svg.scale = 1.
            # svg.center = Window.center

    def clear_canvas(self, obj):
        self.painter.clear_canvas()

    def save_canvas(self, obj):
        self.painter.save_to_svg()

    def on_pause(self):
        return True


if __name__ == "__main__":
    TouchtracerApp().run()
