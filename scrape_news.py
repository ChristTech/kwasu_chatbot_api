import requests
from bs4 import BeautifulSoup
import sqlite3

def scrape_allschool_ng():
    url = "https://allschool.ng/tag/kwasu/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    news_items = []
    for article in soup.find_all("article"):  # Loop through each article
        title_element = article.find("p", class_="ast-blog-single-element ast-read-more-container read-more")
        date_element = article.find("span", class_="published")
        # link_element = article.find("a", class_="")
        # content_element = article.find("p", class_="ast-blog-single-element ast-read-more-container read-more")
        
        # Ensure all required elements are found
        if title_element and date_element:
            title = title_element.text.strip()
            date = date_element.text.strip()
            # content = content_element.text.strip()

            cleaned_title = title.replace('Read Post »', '')
            
            link = f'https://allschool.ng/{title}/'.replace('Read Post', '').replace(' ', '-')
            cleaned_link = link.replace(",", "").replace("’", "")
            cleaned_link = cleaned_link[:-4].lower()
            
            
            news_items.append({
                "title": cleaned_title,
                "date": date,
                "link": cleaned_link,
                # "content": content
            })
    return news_items


# Function to save news to SQLite database
def save_to_database(news_items):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("news_updates.db")
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        link TEXT UNIQUE NOT NULL
    )
    """)
    
    # Insert news items into the database
    for item in news_items:
        try:
            cursor.execute("""
            INSERT INTO news_updates (title, date, link)
            VALUES (?, ?, ?)
            """, (item["title"], item["date"], item["link"]))
            print(f"Added to database: {item['title']}")
        except sqlite3.IntegrityError:
            print(f"Duplicate link skipped: {item['link']}")
    
    # Commit changes and close the connection
    conn.commit()
    conn.close()

# Main execution
news_items = scrape_allschool_ng()
save_to_database(news_items)
