import webbrowser
import sqlite3
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from openai import OpenAI
import requests
import json
from geopy.distance import geodesic
import time
from plyer import gps
import platform

from kivy.vector import Vector
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
import asynckivy
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.behaviors import TouchBehavior
from kivymd.app import MDApp
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from KivyMD.kivymd.uix.fitimage.fitimage import FitImage
from KivyMD.kivymd.uix.label.label import MDLabel
from kivy.garden.mapview import MapView, MapMarker, MapLayer
from kivy.graphics import Color, Line

from KivyMD.kivymd.uix.snackbar.snackbar import MDSnackbar, MDSnackbarText


class Command(MDLabel):
    text = StringProperty()
    size_hint_x = NumericProperty()
    halign = StringProperty
    font_size = 17

class Response(MDLabel):
    text = StringProperty()
    size_hint_x = NumericProperty()
    halign = StringProperty
    font_size = 17
    allow_copy=True

class BaseMDNavigationItem(MDNavigationItem):
    icon = StringProperty()
    text = StringProperty()
    adaptive_height = BooleanProperty()
    spacing = StringProperty()


class BaseScreen(MDScreen):
    image_size = StringProperty()


class NewsItem(MDBoxLayout):
    title = StringProperty()
    date = StringProperty()
    link = StringProperty()

    def open_link(self):
        webbrowser.open(self.link)


def setup_database():
    conn = sqlite3.connect("news_updates.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            link TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def fetch_news():
    conn = sqlite3.connect("news_updates.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, date, link FROM news_updates ORDER BY id ASC")
    news_items = cursor.fetchall()

    conn.close()
    return news_items


######################################################################################################
######################### chatbot section ########################################

# Load FAISS index once
index = faiss.read_index("faiss_index.bin")

API_KEY = "" # Replace with your actual API key

url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


# Load chunks once
with open('temp_documents.txt', 'r', encoding='utf-8') as file:
    chunks = [chunk.strip() for chunk in file.read().split("\n\n") if chunk.strip()]

# Load embedding model once
embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')

def get_context(query, top_k=1):  # Reduce top_k to 1 or 2
    """
    Retrieves relevant chunks based on the query, limiting text length for efficiency.

    Args:
        query (str): The user's question.
        top_k (int): Number of relevant chunks to retrieve.
        max_sentences (int): Maximum number of sentences to return from each chunk.

    Returns:
        str: Concise relevant context.
    """

    query_embedding = embedding_model.encode([query]).astype('float32')
    distances, indices = index.search(query_embedding, top_k)

    # Get unique non-empty chunks
    retrieved_chunks = list(set(chunks[i].strip() for i in indices[0] if chunks[i].strip()))

    context = "\n".join(retrieved_chunks[:1])  # Limit to 1-2 chunks
    return f'"""\n{context}\n"""' if context else '"""\nNo relevant information found.\n"""'

# Function to check if the retrieved context is meaningful
def is_context_valid(context):
    """Returns True if the context contains meaningful information."""
    word_count = len(context.split())
    return word_count > 5 and len(context) > 50  # Ensures it has at least a sentence


def get_chatbot_response(query, previous_messages=None):
    context = get_context(query)
    context = context[:700]
    print(context)

    if not is_context_valid(context):
        print("⚠️ Context is too vague. Defaulting to model's general knowledge.")
        context = ""

    # Construct messages
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant that only gives answers to questions about Kwara State University, nothing else."}
    ]
    
    # Include previous conversation history if available
    if previous_messages:
        messages.extend(previous_messages)

    # Add user query with context
    messages.append({"role": "user", "content": f"Context: {context}\nQuestion: {query}"})

    # API request payload
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": messages,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        result = response.json()

        # Extract and print the response
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        print(result)

        return answer

    except requests.exceptions.Timeout:
        return "Request timed out. Please check your internet connection and try again."

    except requests.exceptions.ConnectionError:
        return "Network error. Please check your internet connection."

    except requests.exceptions.RequestException as e:
        return f"API error: {str(e)}"


######################################################################################################

# OpenRouteService API Key (Replace with your own key)
ORS_API_KEY = ""

class RouteLayer(MapLayer):
    """
    Custom MapLayer that draws a route as a red polyline.
    The 'points' property should be a flat list of screen coordinates.
    """
    def __init__(self, points, **kwargs):
        super().__init__(**kwargs)
        self.points = points

    def reposition(self):
        # When the map moves or zooms, we clear and redraw the line.
        map_view = self.parent
        if not map_view:
            return
        self.canvas.clear()
        with self.canvas:
            Color(1, 0, 0, 1)  # Red color for the route
            # Here, self.points is already in screen coordinates.
            if len(self.points) >= 4:
                Line(points=self.points, width=2)


class KwasuChatNav(MDApp):
    is_initialized = False
    initial_touch_pos = None  # Track where the touch started
    map_sources = {
        "street": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    }
    current_map = StringProperty("street")
    markers = []  # Track marker widgets
    route_layer = None
    simulation_active = False
    user_marker = None
    destination_marker = None
    gps_active = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.platform = platform.system()

    def my_touch_down(self, instance, touch):
        """Capture initial touch position if on the map"""
        map_view = self.root.ids.map_view
        if map_view.collide_point(*touch.pos):
            self.initial_touch_pos = touch.pos
            print(f"Touch Down: {touch.pos}")  # Debugging

        #return True

    def on_map_zoom(self, instance, zoom):
        """Redraw the route when the map is zoomed"""
        if self.markers and len(self.markers) == 2:
            start = (self.markers[0].lat, self.markers[0].lon)
            end = (self.markers[1].lat, self.markers[1].lon)
            self.draw_route(start, end)


    def get_route(self, start, end):
        """Fetch route from OpenRouteService API"""
        url = (f"https://api.openrouteservice.org/v2/directions/foot-walking?"
               f"api_key={ORS_API_KEY}&start={start[1]},{start[0]}&end={end[1]},{end[0]}")
        response = requests.get(url, timeout=10)
        try:
            route_data = response.json()
            if "features" not in route_data or not route_data["features"]:
                print("⚠️ No route found")
                return

            coordinates = route_data["features"][0]["geometry"]["coordinates"]
            self.draw_route([(coord[1], coord[0]) for coord in coordinates])

        except requests.exceptions.ConnectTimeout:
            MDSnackbar(
                    MDSnackbarText(
                        text="There's an issue with getting your route at this moment.",
                    ),
                    y='24dp',
                    pos_hint={"center_x": 0.5},
                    size_hint_x=0.8,
                ).open()
            
            print("There's an issue with getting your route at this moment")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            MDSnackbar(
                MDSnackbarText(
                    text=f"An error occurred while fetching the route: {e}",
                ),
                y='24dp',
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
            ).open()

    def calculate_distance(self, point1, point2):
        """Calculate geodesic distance between two (lat, lon) points"""
        return geodesic(point1, point2).meters  # Distance in meters
    
    def show_distance_snackbar(self, distance):
        """Display distance using MDSnackbar"""
        MDSnackbar(
            MDSnackbarText(
                text=f"Distance: {distance:.2f} meters",
            ),
            y='24dp',
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
        ).open()

    def draw_route(self, points):
        """Convert points and draw route layer"""
        map_view = self.root.ids.map_view

        try:
            if self.route_layer:
                map_view.remove_widget(self.route_layer)

            screen_points = []
            for lat, lon in points:
                x, y = map_view.get_window_xy_from(lat, lon, map_view.zoom)
                screen_points.extend([x, y])
            
            if len(screen_points) >= 4:
                self.route_layer = RouteLayer(screen_points)
                map_view.add_widget(self.route_layer)

        except:
            print("An error occured while getting route information")

    def add_marker_on_click(self, instance, touch):
        """Add marker with 2-marker limit"""
        map_view = self.root.ids.map_view
        
        if touch.is_mouse_scrolling or not map_view.collide_point(*touch.pos):
            return
        
        # Check if this was a drag (movement > 10 pixels)
        if self.initial_touch_pos:
            distance_moved = Vector(touch.pos).distance(self.initial_touch_pos)
            print(f"Touch Pos: {touch.pos}, Initial Touch Pos: {self.initial_touch_pos}, Distance Moved: {distance_moved}")  # Debugging

            if distance_moved > 10:  # 10-pixel threshold for drag detection
                self.initial_touch_pos = None
                print("Drag detected, cancelling marker placement")  # Debugging

                return  # Cancel marker placement

        # Get coordinates
        local_x, local_y = map_view.to_local(*touch.pos, relative=True)
        lat, lon = map_view.get_latlon_at(local_x, local_y)
        
        # Remove existing markers if starting new pair
        if len(self.markers) >= 2:
            for marker in self.markers:
                map_view.remove_widget(marker)
            self.markers.clear()
            if self.route_layer:
                map_view.remove_widget(self.route_layer)
                self.route_layer = None

        # Add new marker
        marker = MapMarker(lat=lat, lon=lon, source='marker.png')
        map_view.add_widget(marker)
        map_view.zoom = 16
        self.markers.append(marker)
        
        # Draw route when we have 2 markers
        if len(self.markers) == 2:
            start = (self.markers[0].lat, self.markers[0].lon)
            end = (self.markers[1].lat, self.markers[1].lon)

            distance = self.calculate_distance(start, end)
            self.show_distance_snackbar(distance)
            self.get_route(start, end)

            # Start simulation or GPS updates based on platform
            if self.platform == "Windows":
                self.start_simulation()
            else:
                self.start_gps_updates(end)

        self.initial_touch_pos = None  # Reset for next touch


    def start_simulation(self):
        """Start simulating the user moving from the first marker to the second marker"""
        if len(self.markers) == 2 and not self.simulation_active:
            self.simulation_active = True
            self.user_marker = self.markers[0]
            self.destination_marker = self.markers[1]
            Clock.schedule_interval(self.simulate_movement, 0.5)  # Update every 1 second

    
    def simulate_movement(self, dt):
        """Simulate the user moving towards the destination"""
        if not self.user_marker or not self.destination_marker:
            Clock.unschedule(self.simulate_movement)
            self.simulation_active = False
            return

        user_lat, user_lon = self.user_marker.lat, self.user_marker.lon
        dest_lat, dest_lon = self.destination_marker.lat, self.destination_marker.lon

        # Calculate a small step towards the destination
        step_size = 0.01  # Adjust this value to control the speed of the simulation
        new_lat = user_lat + step_size * (dest_lat - user_lat)
        new_lon = user_lon + step_size * (dest_lon - user_lon)

        self.user_marker.lat = new_lat
        self.user_marker.lon = new_lon
        self.root.ids.map_view.center_on(new_lat, new_lon)

        # Calculate distance to destination
        distance = self.calculate_distance((new_lat, new_lon), (dest_lat, dest_lon))
        self.show_distance_snackbar(distance)

        # Update the route line by creating a list with the current user and destination coordinates
        points = [(new_lat, new_lon), (dest_lat, dest_lon)]
        self.draw_route(points)

        # Check if the user has reached the destination
        if distance < 5:  # Adjust this value to control the arrival threshold
            self.show_arrival_message()
            Clock.unschedule(self.simulate_movement)
            self.simulation_active = False

    def start_gps_updates(self, destination):
        """Start GPS updates and set the destination"""
        self.destination = destination
        try:
            gps.configure(on_location=self.update_location)
            gps.start(minTime=1000, minDistance=1)
            self.gps_active = True
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.gps_status = "GPS is not implemented for your platform"

    def stop_gps_updates(self):
        """Stop GPS updates"""
        if self.gps_active:
            gps.stop()
            self.gps_active = False

    def update_location(self, **kwargs):
        """Update user location and distance to destination"""
        lat = kwargs['lat']
        lon = kwargs['lon']
        self.user_marker.lat = lat
        self.user_marker.lon = lon
        self.root.ids.map_view.center_on(lat, lon)

        # Calculate distance to destination
        distance = self.calculate_distance((lat, lon), self.destination)
        self.show_distance_snackbar(distance)

        # Update the route line
        points = [(lat, lon), self.destination]
        self.draw_route(points)

        # Check if the user has reached the destination
        if distance < 5:
            self.show_arrival_message()
            self.stop_gps_updates()

    def add_current_location(self):
        """Add current location as the first marker"""
        if self.platform == "Windows":
            MDSnackbar(
                MDSnackbarText(
                    text="This feature is not available on Windows.",
                ),
                y='24dp',
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
            ).open()
            return

        try:
            gps.configure(on_location=self.set_current_location)
            gps.start(minTime=1000, minDistance=1)
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.gps_status = "GPS is not implemented for your platform"

    def set_current_location(self, **kwargs):
        """Set current location as the first marker and stop GPS"""
        gps.stop()
        lat = kwargs['lat']
        lon = kwargs['lon']

        # Remove existing markers
        for marker in self.markers:
            self.root.ids.map_view.remove_widget(marker)
        self.markers.clear()
        if self.route_layer:
            self.root.ids.map_view.remove_widget(self.route_layer)
            self.route_layer = None

        # Add new marker at current location
        marker = MapMarker(lat=lat, lon=lon, source='marker.png')
        self.root.ids.map_view.add_widget(marker)
        self.root.ids.map_view.zoom = 16
        self.markers.append(marker)

        MDSnackbar(
            MDSnackbarText(
                text="Current location added as the first marker. Click on the map to add destination.",
            ),
            y='24dp',
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
        ).open()


    def show_arrival_message(self):
        """Display a message when the user has arrived at the destination"""
        MDSnackbar(
            MDSnackbarText(
                text="Successfully arrived at destination!",
            ),
            y='24dp',
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
        ).open()


    def on_switch_tabs(self, bar, item, item_icon, item_text):
        self.root.ids.screen_manager.current = item_text

    def send_message(self):
        user_input = str(self.root.ids.user_input.text.strip())
        user_input = user_input.lower()

        if user_input:
            user_message = Command(
                text=user_input,
                size_hint_x=0.75,
                pos_hint={"right": 0.98},
                allow_copy=True
            )
            self.root.ids.chat_list.add_widget(user_message)

            user_input = user_input.replace("vc", "vice chancellor").replace('kwasu', 'kwara state university')


            bot_message = Response(
                text = f"{get_chatbot_response(user_input)}",
                size_hint_x=0.75,
                pos_hint={"x": 0.02},
                allow_copy=True
            )

            self.root.ids.chat_list.add_widget(bot_message)

            self.root.ids.chat_scroll.scroll_to(user_message)
            self.root.ids.user_input.text = ""

    def search_news(self):
        search_term = self.root.ids.search_input.text.strip()
        if not search_term:
            conn = sqlite3.connect("news_updates.db")
            cursor = conn.cursor()

            cursor.execute("SELECT title, date, link FROM news_updates ORDER BY date DESC")
            news_items = cursor.fetchall()

            
            # Update the news list
            news_list = self.root.ids.news_list
            news_list.clear_widgets()

            for title, date, link in news_items:
                news_list.add_widget(NewsItem(title=title, date=date, link=link))

            conn.close()
            return news_items # If the search field is empty, do nothing

        conn = sqlite3.connect("news_updates.db")
        cursor = conn.cursor()

        query = """
            SELECT title, date, link 
            FROM news_updates 
            WHERE title LIKE ? 
            ORDER BY date ASC
        """
        cursor.execute(query, (f"%{search_term}%",))
        news_items = cursor.fetchall()
        conn.close()

        # Update the news list
        news_list = self.root.ids.news_list
        news_list.clear_widgets()

        for title, date, link in news_items:
            news_list.add_widget(NewsItem(title=title, date=date, link=link))

        if not news_items:
            # Display a message if no news matches the search
            news_list.add_widget(MDLabel(text="No results found.", halign="center"))


    def set_active_element(self, instance, type_map):
        for element in self.root.ids.content_container.children:
            if instance == element:
                element.selected = True
                self.current_map = type_map
            else:
                element.selected = False


    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Mediumseagreen"
        screen = Builder.load_file('main_app.kv')

        if not KwasuChatNav.is_initialized:
            setup_database()

            KwasuChatNav.is_initialized = True

        screen.ids.news_list.clear_widgets()
        news_items = fetch_news()


        for item in news_items:
            id, title, date, link = item
            screen.ids.news_list.add_widget(
                NewsItem(title=title, date=date, link=link),
            )

        # Bind add_marker_on_click to the on_touch_up event of the MapView
        map_view = screen.ids.map_view
        map_view.bind(on_touch_down=self.my_touch_down) # Bind on_touch_down here
        map_view.bind(on_touch_down=self.add_marker_on_click)
        map_view.bind(on_zoom=self.on_map_zoom) # Bind on_zoom event


        self.user_marker = MapMarker(lat=0, lon=0, source='user_marker.png')
        map_view.add_widget(self.user_marker)

        return screen


        
KwasuChatNav().run()
