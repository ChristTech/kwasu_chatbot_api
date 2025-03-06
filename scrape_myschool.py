import sqlite3
import requests
from bs4 import BeautifulSoup

# Database setup for the new data
def setup_new_database():
    conn = sqlite3.connect("news_scrape.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kwasu_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            link TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Function to scrape data
def scrape_website():
    url = "https://myschool.ng/news"  # URL of the website to scrape
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        news_items = []

        # Extract news blocks
        news_blocks = soup.find_all("div", class_="mb-2")

        for block in news_blocks:
            # Extract the title and link
            title_link = block.find("a")
            title = title_link.text.strip()
            link = title_link["href"]

            # Extract the date
        
            date = title_link.find("small", class_="text-muted").text.strip()

            news_items.append((title, date, link))

        return news_items
    else:
        print(f"Failed to fetch the page. Status code: {response.status_code}")
        return []

# Store scraped data into the database
def store_scraped_data(news_items):
    conn = sqlite3.connect("news_scrape.db")
    cursor = conn.cursor()

    for title, date, link in news_items:
        cursor.execute("""
            INSERT INTO kwasu_news (title, date, link)
            VALUES (?, ?, ?)
        """, (title, date, link))

    conn.commit()
    conn.close()

# Main function to run the scraper
if __name__ == "__main__":
    setup_new_database()
    news_items = scrape_website()
    if news_items:
        store_scraped_data(news_items)
        print(f"Scraped and stored {len(news_items)} news items successfully.")
    else:
        print("No news items found.")
