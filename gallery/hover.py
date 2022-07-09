"""Hoverable Behaviour (changing when the mouse is on the widget by O. Poyen.
Edit by kuzeyron
License: LGPL
"""
__author__ = 'Olivier POYEN'

from kivy.core.window import Window
from kivy.factory import Factory
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.utils import platform


class HoverBehavior:
    hovered = BooleanProperty(False)
    border_point = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')

        if platform in ('win', 'linux', 'mac') and self.hover:
            Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return  # do proceed if I'm not displayed <=> If have no parent

        pos = args[1]
        # Next line to_widget allow to compensate for relative layout
        inside = self.collide_point(*self.to_widget(*pos))

        if self.hovered == inside:
            # We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside

        if inside:
            self.dispatch('on_enter')
        else:
            self.dispatch('on_leave')

    def on_enter(self):
        pass

    def on_leave(self):
        pass


Factory.register('HoverBehavior', HoverBehavior)


if __name__ == '__main__':
    from textwrap import dedent

    from kivy.base import runTouchApp
    from kivy.lang import Builder
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.label import Label

    Builder.load_string(dedent('''
    <HoverLabel>:
        text: "inside" if self.hovered else "outside"
        pos: 200,200
        size_hint: None, None
        size: 100, 30
        canvas.before:
            Color:
                rgb: 1,0,0
            Rectangle:
                size: self.size
                pos: self.pos
    '''))

    class HoverLabel(Label, HoverBehavior):
        def on_enter(self, *largs):
            print("You are in, through this point", self.border_point)

        def on_leave(self, *largs):
            print("You left through this point", self.border_point)

    fl = FloatLayout()
    fl.add_widget(HoverLabel())
    runTouchApp(fl)
