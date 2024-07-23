import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import openai
import os
from dotenv import load_dotenv
import tiktoken
from db_connection import connect_to_database, store_document_chunk

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("OpenAI API key is not set in the environment variables.")

def is_valid_link(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ['http', 'https']:
        return False
    if any(domain in parsed_url.netloc for domain in ['youtube.com', 'facebook.com', 'twitter.com']):
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

def split_text_into_chunks(text, max_tokens=4000):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    chunks = []

    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)

    return chunks

def store_document_chunks(conn, url, text, bot_id):
    chunks = split_text_into_chunks(text)
    for chunk in chunks:
        embedding = calculate_embedding(chunk)
        if embedding is None:
            print(f"Failed to calculate embedding for chunk from {url}.")
            continue
        
        try:
            store_document_chunk(conn, bot_id, url, chunk, embedding)
            print(f"Stored document from {url}")
        except Exception as e:
            print(f"Error storing chunk from {url}: {e}")

def crawl_website(bot_id, url, max_depth=2):
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
                    conn = connect_to_database()
                    if conn:
                        store_document_chunks(conn, current_url, text, bot_id)
                        conn.close()

                for link in soup.find_all('a', href=True):
                    absolute_link = urljoin(current_url, link['href'])

                    if is_valid_link(absolute_link) and absolute_link not in visited_urls:
                        visited_links.append(absolute_link)
                        recursive_crawl(absolute_link, depth - 1)
        except Exception as e:
            print(f"Error crawling {current_url}: {e}")

    recursive_crawl(url, max_depth)

    print("\nVisited Links:")
    for i, link in enumerate(visited_links, 1):
        print(f"{i}. {link}")
    print(f"\nTotal Links Visited: {len(visited_links)}")

if __name__ == "__main__":
    pass
