import webview
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

class WebviewApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        open_map_button = Button(text="Open Google Maps (KWASU)")
        open_map_button.bind(on_press=self.open_map)
        layout.add_widget(open_map_button)
        return layout

    def open_map(self, instance):
        # Google Maps URL with coordinates for KWASU, with a zoom level
        url = "https://www.google.com/maps?q=8.5854,4.5683&z=17"
        
        # Open the webview with the specified URL
        webview.create_window("Kwara State University Map", url)
        webview.start()

if __name__ == "__main__":
    WebviewApp().run()
