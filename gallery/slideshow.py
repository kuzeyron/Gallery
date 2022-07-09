from functools import partial
from os import listdir
from os.path import isfile, join, splitext
from random import randint
from threading import Thread

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.lang import Builder
from kivy.properties import (BooleanProperty, ListProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.uix.scatter import Scatter

from kivy.uix.floatlayout import FloatLayout

__all__ = ['SlideShow', 'Slide']

Builder.load_string('''
<Slide>:
    size_hint: None, None
    canvas:
        Color:
            rgb: 1, 1, 1
        RoundedRectangle:
            radius: (self.corner_radius, )
            size: self.size
            pos: self.pos
        StencilPush
        RoundedRectangle:
            radius: [self.corner_radius, ]
            size: self.size[0] - dp(10), self.size[1] - root.border_width
            pos: self.pos[0] + dp(5), self.pos[1] + root.border_width / 2
        StencilUse
        Rectangle:
            texture: self._image.texture if self._image else None
            size: self.size
            pos: self.pos
        StencilUnUse
        RoundedRectangle:
            radius: (self.corner_radius, )
            size: self.size[0] - dp(10), self.size[1] - root.border_width
            pos: self.pos[0] + dp(5), self.pos[1] + root.border_width / 2
        StencilPop
''')


class Slide(Scatter):
    _fake_delay = NumericProperty()
    _image = ObjectProperty()
    _orig_pos = ListProperty((0, 0))
    _orig_rot = NumericProperty(90)
    _orig_size = ListProperty((0, 0))
    border_width = NumericProperty('10dp')
    corner_radius = NumericProperty()
    filename = StringProperty()
    image_ratio = NumericProperty(1.)
    keep_ratio = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._image = CoreImage(self.filename)
        self.bind(size=self.layout_changes)

    def on_kv_post(self, *largs):
        self._orig_size = self.size
        self._orig_rot = self.rotation
        self._orig_pos = self.pos
        Clock.schedule_once(self.layout_changes, 0)

    def layout_changes(self, *largs):
        self.image_ratio = self._image.width / float(self._image.height)
        self.height = self.width / self.image_ratio


class SlideShow(FloatLayout):
    allowed_exts = ListProperty(['.png', '.jpg', '.jpeg', '.webp'])
    collection = ListProperty()
    folder = StringProperty()
    delay = NumericProperty(2)
    wait_time = NumericProperty(5)

    def on_kv_post(self, *largs):
        Thread(target=self.add_source, daemon=True).start()
        Clock.schedule_once(self.picture_looper, self.delay)
        self.bind(folder=self.add_source)

    def add_source(self, directory=None, dt=0):
        """ Scans selected folder, adds the widgets
            for all found pictures, then adds the
            paths to the collection list """
        directory = directory or self.folder

        for index, filename in enumerate(listdir(directory), 1):
            path = join(directory, filename)
            _, ext = splitext(filename)

            if all([
                path not in self.collection,
                ext in self.allowed_exts,
                isfile(path)
            ]):
                self.collection.append(path)
                Clock.schedule_once(
                    partial(self.add_slide, path),
                    .2 + index / 10  # Delay when adding
                )

    def add_slide(self, path, *largs):
        self.add_widget(
            Slide(
                filename=path,
                width=self.width / 3.5,  # Feel free to change
                rotation=randint(-30, 30),
                pos=(randint(0, 200), randint(0, 200))
            )
        )

    def add_sources(self, directories=[], dt=0):
        for folder in directories:
            Clock.schedule_once(
                partial(self.add_source, folder), 0)

    def picture_looper(self, *largs):
        """ This background worker will run even if
            there are no widgets """
        try:
            child = self.children[-1]
            self.remove_widget(child)
            self.add_widget(child)

            ''' Complicated to calculate to set a fixed
                size and center the position '''
            if child.width > child.height:
                e = 3
            else:
                e = 5

            widther = 100 + child.width
            pos = (
                abs((widther / e) - child.x),
                abs((widther / e) - child.y)
            )

            anim = Animation(
                rotation=360 if child._orig_rot >= 180 else 0,
                width=widther,
                pos=pos,
                t='out_back',
                d=.8,
            ) + Animation(
                _fake_delay=1,
                d=self.wait_time
            ) + Animation(
                rotation=child._orig_rot,
                size=child._orig_size,
                pos=child._orig_pos,
                _fake_delay=0,
                d=.5,
            )
            anim.bind(on_complete=self.picture_looper)
            anim.start(child)

        except Exception:
            # Ignore if there are no widgets
            pass
