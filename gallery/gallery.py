from functools import partial
from os import listdir
from os.path import isfile, join, splitext

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.lang import Builder
from kivy.properties import (BooleanProperty, ListProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.uix.checkbox import CheckBox
from kivy.uix.stacklayout import StackLayout

from gallery.hover import HoverBehavior

__all__ = ['PhotoGallery', 'Picture', ]

Builder.load_string('''
<Picture>:
    size_hint: None, None
    group: None if self.multiselection else True
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
            texture: self.preview_texture.texture \
                     if self.preview_texture else None
            size:
                self.size[0] + self.zoom, \
                self.size[1] + (self.zoom / self.image_ratio)
            pos:
                self.pos[0] - int(self.zoom / 2), \
                self.pos[1] - int(self.zoom / 2 / self.image_ratio)
        StencilUnUse
        RoundedRectangle:
            radius: (self.corner_radius, )
            size: self.size[0] - dp(10), self.size[1] - root.border_width
            pos: self.pos[0] + dp(5), self.pos[1] + root.border_width / 2
        StencilPop
        Color:
            rgba: (.25, .15, .25, .7) if self.active else (1, 1, 1, 0)
        RoundedRectangle:
            radius: (dp(5), )
            size: self.size[0] - dp(10), self.size[1] - root.border_width
            pos: self.pos[0] + dp(5), self.pos[1] + root.border_width / 2
        Color:
            rgba: (1, 1, 1, 1 if self.active else 0)
        Line:
            cap: 'square'
            joint: 'miter'
            points: [ \
                (self.center_x - 15, self.center_y - 12 + root.border_width), \
                (self.center_x, self.center_y - 25 + root.border_width), \
                (self.center_x + 30, self.center_y + 5 + root.border_width) \
            ]
            width: 5
''')


class Picture(HoverBehavior, CheckBox):
    anim = ObjectProperty()
    border_width = NumericProperty('10dp')
    corner_radius = NumericProperty()
    filename = StringProperty()
    image_ratio = NumericProperty(1.)
    keep_ratio = BooleanProperty(True)
    preview_texture = ObjectProperty()
    zoom = NumericProperty()
    multiselection = BooleanProperty(None)
    hover = BooleanProperty(True)
    zoom_level = NumericProperty('200dp')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.preview_texture = CoreImage(self.filename)
        self.anim = Animation()
        self.bind(
            size=self.layout_changes,
            active=self.toggle_zoom
        )
        Clock.schedule_once(self.layout_changes, 0)

    def layout_changes(self, *largs):
        pt = self.preview_texture
        self.image_ratio = pt.width / float(pt.height)
        self.height = self.width / self.image_ratio

    def on_enter(self, *largs):
        if not self.active and self.hover:
            Clock.schedule_once(self.animate, 0)

    def toggle_zoom(self, *largs):
        sel = self.parent.selected
        if self.active:
            sel.append(self.filename)
            Clock.schedule_once(self.on_leave, 0)
        else:
            sel.pop(sel.index(self.filename))
            Clock.schedule_once(self.on_enter, 0)

    def on_leave(self, *largs):
        self.anim.cancel(self)
        self.zoom = 0

    def animate(self, *largs):
        self.anim = Animation(zoom=self.zoom_level, t='out_back', d=.3)
        self.anim.start(self)


class PhotoGallery(StackLayout):
    allowed_exts = ListProperty(['.png', '.jpg', '.jpeg', '.webp'])
    border_width = NumericProperty('10dp')
    collection = ListProperty()
    corner_radius = NumericProperty('5dp')
    folder = StringProperty()
    multiselection = BooleanProperty(None, allownone=True)
    rows = NumericProperty(2)
    selected = ListProperty()
    hover = BooleanProperty(True)
    orientation = StringProperty('lr-tb')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # We want the layout being ready. This is wrong
        Clock.schedule_once(lambda dt: self._collect(), .5)

    def width_calculation(self):
        """ Sums together the spacing/padding and match
            that with amount of rows """
        sr = sum(self.spacing[::2] + self.padding[::2]) * self.rows
        return (self.width - sr) / self.rows

    def _collect(self, directory=None, *largs):
        """ Main core """
        directory = directory or self.folder
        width = self.width_calculation()

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
                    partial(self.add_picture, path, width),
                    index / 20
                )

    def add_picture(self, path, width, *largs):
        self.add_widget(
            Picture(
                filename=path,
                width=width,
                corner_radius=self.corner_radius,
                border_width=self.border_width,
                multiselection=self.multiselection,
                hover=self.hover
            )
        )

    def add_collection(self, folder, *largs):
        """ Add content """
        Clock.schedule_once(partial(self._collect, folder), 0)

    def empty_collection(self, *largs):
        """ Similar to self.clear_widgets """
        Clock.schedule_once(partial(self.remove_picture, rm_all=True), 0)

    def remove_picture(self, path=None, rm_all=False, *largs):
        """ loop through children and find the path to remove """
        for index, child in enumerate(self.children):
            if rm_all or child.filename == path:
                anim = Animation(opacity=0, d=index / 10, t='out_back')
                anim.bind(on_complete=self._rm_picture)
                anim.start(child)

    def _rm_picture(self, anim, child):
        """" Internal use only """
        if child.filename in self.selected:
            self.selected.pop(self.selected.index(child.filename))
        self.remove_widget(child)
        self.collection.pop(self.collection.index(child.filename))

    def recompute_layout(self, *largs):
        """ Giving the width for the children """
        width = self.width_calculation()
        for child in self.children:
            child.width = width
