from kivy.app import App
from kivy.lang import Builder
from kivy.uix.scrollview import ScrollView

Builder.load_string('''
#:import PhotoGallery gallery.PhotoGallery
#:import SlideShow gallery.SlideShow

<Application>:
    do_scroll_x: False
    BoxLayout:
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
        spacing: dp(10)

        BoxLayout:
            size_hint_y: None
            height: root.height / 1.7
            orientation: 'vertical'
            spacing: dp(5)
            ScrollView:
                do_scroll_x: False
                PhotoGallery:
                    folder: 'demos'
                    size_hint_y: None
                    height: self.minimum_height
                    multiselection: True
                    id: gallery
                    rows: 3
                    spacing: dp(5)
            Slider:
                size_hint_y: .1
                min: 1
                max: 5
                value: gallery.rows
                on_value:
                    gallery.rows = self.value
                    gallery.recompute_layout()
            Label:
                text: f"Selected pictures: {len(gallery.selected)}"
                size_hint_y: .1

        SlideShow:
            size_hint_y: None
            height: root.height
            folder: 'pictures'
''')


class Application(ScrollView):
    pass


class TestApp(App):

    def build(self):
        return Application()


if __name__ == '__main__':
    TestApp().run()
