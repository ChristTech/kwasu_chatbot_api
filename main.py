import webbrowser
import sqlite3
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from openai import OpenAI
import requests
import json


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
from kivy.garden.mapview import MapView, MapMarker


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

    cursor.execute("SELECT title, date, link FROM news_updates ORDER BY date ASC")
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


def get_chatbot_response(query):

    context = get_context(query)
    context = context[:700]
    print(context)

    if not is_context_valid(context):
        print("⚠️ Context is too vague. Defaulting to model's general knowledge.")
        context = ""

    data = {
    "model": "mixtral-8x7b-32768",
    "messages": [
        {"role": "system", "content": "You are a helpful AI assistant that only gives answers to questions about kwara state university, nothing else."},
        {"role": "user", "content": f"Context: {context}\nQuestion: {query}"}
    ],
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



class Example(MDApp):
    is_initialized = False
    map_sources = {
        "street": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    }
    
    current_map = StringProperty("street")

    def open_menu(self, item):
        menu_items = [
            {
                "text": f"{locations}",
                "on_release": lambda x=f"{locations}": self.menu_callback(x),
            } for locations in ["ICT", 'FMSS', 'Engineering', 'HMSS']
        ]
        MDDropdownMenu(caller=item, items=menu_items).open()

    def menu_callback(self, text_item):
        self.root.ids.drop_text.text = text_item
        self.add_marker(8.717236, 4.477021)

    def disable_dropdown(self):
        print('dropdown disabled')

    def add_marker(self, lat, lon):
        marker = MapMarker(lat=lat, lon=lon, source="libs\garden\garden.mapview\mapview\icons\marker.png")  # Use a custom marker image if needed
        self.root.ids.map_view.add_widget(marker)


    def on_switch_tabs(self, bar, item, item_icon, item_text):
        self.root.ids.screen_manager.current = item_text

    def send_message(self):
        user_input = str(self.root.ids.user_input.text.strip())
        user_input = user_input.lower()

        if user_input:
            user_message = Command(
                text=user_input,
                size_hint_x=0.75,
                pos_hint={"right": 0.98}
            )
            self.root.ids.chat_list.add_widget(user_message)

            user_input = user_input.replace("vc", "vice chancellor").replace('kwasu', 'kwara state university')


            bot_message = Response(
                text = f"{get_chatbot_response(user_input)}",
                size_hint_x=0.75,
                pos_hint={"x": 0.02}
            )

            self.root.ids.chat_list.add_widget(bot_message)

            self.root.ids.chat_scroll.scroll_to(user_message)
            self.root.ids.user_input.text = ""

    def search_news(self):
        search_term = self.root.ids.search_input.text.strip()
        if not search_term:
            conn = sqlite3.connect("news_updates.db")
            cursor = conn.cursor()

            cursor.execute("SELECT title, date, link FROM news_updates ORDER BY date ASC")
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

        if not Example.is_initialized:
            setup_database()

            Example.is_initialized = True

        screen.ids.news_list.clear_widgets()
        news_items = fetch_news()


        for item in news_items:
            title, date, link = item
            screen.ids.news_list.add_widget(
                NewsItem(title=title, date=date, link=link),
            )

        return screen


Example().run()
