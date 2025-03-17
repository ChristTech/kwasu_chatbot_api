import requests
import json
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.garden.mapview import MapView, MapMarker, MapLayer
from kivy.graphics import Color, Line

# Replace with your actual OpenRouteService API key
ORS_API_KEY = "5b3ce3597851110001cf6248918137aedf074db7bfb2d3673dcb58d6"

KV = """
BoxLayout:
    orientation: "vertical"
    MapView:
        id: main_map
        zoom: 15
        lat: 8.717236
        lon: 4.477021
        on_touch_down: app.on_map_touch(*args)
    Label:
        id: info_label
        size_hint_y: None
        height: 50
        text: "Tap on the map to set start & destination."
"""

class RouteLayer(MapLayer):
    """Custom MapLayer to draw the route (a red line) on the map."""
    def __init__(self, points, **kwargs):
        super(RouteLayer, self).__init__(**kwargs)
        self.points = points  # This should be a list of (lat, lon) pairs

    def reposition(self):
        """Redraws the route whenever the map is moved or zoomed."""
        mapview = self.parent
        if not mapview:
            return
        self.canvas.clear()
        with self.canvas:
            Color(1, 0, 0, 1)  # Red color for the route
            screen_points = []
            # Convert each (lat, lon) into window (x, y) coordinates
            for lat, lon in self.points:
                x, y = mapview.get_window_xy_from(lat, lon, mapview.zoom)
                screen_points.extend([x, y])
            if len(screen_points) >= 4:
                Line(points=screen_points, width=2)

class MapSearchApp(App):
    first_marker = None  # Will store (lat, lon) for the first tap
    route_layer = None   # Holds the current route layer
    route_markers = []   # Holds markers for waypoints (optional)

    def build(self):
        return Builder.load_string(KV)

    def on_map_touch(self, instance, touch):
        map_view = self.root.ids.main_map
        if map_view.collide_point(*touch.pos):
            # Get latitude and longitude from the touch
            lat, lon = map_view.get_latlon_at(*touch.pos)
            marker = MapMarker(lat=lat, lon=lon)
            map_view.add_widget(marker)
            print(f"Added marker at {lat}, {lon}")

            if self.first_marker is None:
                self.first_marker = (lat, lon)
                self.root.ids.info_label.text = "Start point set. Tap destination."
            else:
                second_marker = (lat, lon)
                self.get_route(self.first_marker, second_marker)
                self.first_marker = None
                self.root.ids.info_label.text = "Route drawn. Tap again to start new route."

    def get_route(self, start, end):
        """Fetches a route between start and end using OpenRouteService."""
        # Note: ORS expects coordinates in order: lon,lat
        url = (
            f"https://api.openrouteservice.org/v2/directions/foot-walking?"
            f"api_key={ORS_API_KEY}&start={start[1]},{start[0]}&end={end[1]},{end[0]}"
        )
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("API Response:", json.dumps(data, indent=2))
            # Ensure the response contains route data under 'features'
            if "features" in data and data["features"]:
                # Extract route coordinates (returned as [lon, lat] pairs)
                coordinates = data["features"][0]["geometry"]["coordinates"]
                # Convert to (lat, lon) for our app
                route_points = [(coord[1], coord[0]) for coord in coordinates]
                self.draw_route(route_points)
                self.add_route_markers(route_points)
            else:
                print("⚠️ No route found in the API response.")
        else:
            print("Error fetching route data:", response.text)

    def draw_route(self, points):
        """Draws a route on the map using a custom RouteLayer."""
        map_view = self.root.ids.main_map
        # Remove existing route layer if it exists
        if self.route_layer:
            map_view.remove_widget(self.route_layer)
        self.route_layer = RouteLayer(points)
        map_view.add_widget(self.route_layer)
        # Schedule an update so that the route redraws when map moves/zooms
        Clock.schedule_interval(self.update_route, 1/30)
        print(f"✅ Route drawn with {len(points)} points.")

    def update_route(self, dt):
        """Forces the route layer to reposition/redraw."""
        if self.route_layer:
            self.route_layer.reposition()

    def add_route_markers(self, points):
        """Optionally, adds markers at each waypoint along the route."""
        map_view = self.root.ids.main_map
        # Remove previous route markers
        for m in self.route_markers:
            map_view.remove_widget(m)
        self.route_markers = []
        for lat, lon in points:
            m = MapMarker(lat=lat, lon=lon)
            map_view.add_widget(m)
            self.route_markers.append(m)

if __name__ == "__main__":
    MapSearchApp().run()
