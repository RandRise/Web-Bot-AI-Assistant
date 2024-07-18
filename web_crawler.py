import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import openai
import os
from dotenv import load_dotenv
from db_connection import connect_to_database, store_document

# Load environment variables from .env file
load_dotenv()

# OpenAI API Key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')


def is_valid_link(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ['http', 'https']:
        return False
    if 'youtube.com' in parsed_url.netloc or 'facebook.com' in parsed_url.netloc or 'twitter.com' in parsed_url.netloc:
        return False
    return True


def calculate_embedding(text):
    try:
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def store_document(conn, url, text, bot_id):
    embedding = calculate_embedding(text)
    if embedding is None:
        print(f"Failed to calculate embedding for {url}. Document not stored.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO documents (bot_id, url, text, embeddings) VALUES (%s, %s, %s, %s)",
            (bot_id, url, text, embedding)
        )
        conn.commit()
        cursor.close()
        print(f"Stored document from {url}")
    except Exception as e:
        print(f"Error storing document from {url}: {e}")


def crawl_website(bot_id, url, max_depth=2):  # Add bot_id here
    visited_urls = set()
    visited_links = []

    def recursive_crawl(current_url, depth):
        if current_url in visited_urls or depth <= 0:
            return

        visited_urls.add(current_url)

        try:
            response = requests.get(current_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text(separator='\n', strip=True)

                if text and text not in visited_urls:
                    visited_urls.add(text)
                    store_document(conn, current_url, text, bot_id)

                for link in soup.find_all('a', href=True):
                    absolute_link = urljoin(current_url, link['href'])

                    if is_valid_link(absolute_link) and absolute_link not in visited_urls:
                        visited_links.append(absolute_link)
                        recursive_crawl(absolute_link, depth - 1)
        except Exception as e:
            print(f"Error crawling {current_url}: {e}")

    conn = connect_to_database()
    if not conn:
        return

    recursive_crawl(url, max_depth)
    conn.close()

    print("\nVisited Links:")
    for i, link in enumerate(visited_links, 1):
        print(f"{i}. {link}")
    print(f"\nTotal Links Visited: {len(visited_links)}")


if __name__ == "__main__":
    pass