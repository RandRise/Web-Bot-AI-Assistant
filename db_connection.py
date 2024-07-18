import psycopg2
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection settings from environment variables
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = os.getenv('DATABASE_PORT')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')

def connect_to_database():
    try:
        conn = psycopg2.connect(
            dbname=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_HOST,
            port=DATABASE_PORT
        )
        print("Connected to PostgreSQL database successfully!")
        return conn
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL database:", error)
        return None

def create_documents_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL,
            text TEXT NOT NULL,
            embeddings FLOAT8[]
        )
        """)
        conn.commit()
        cursor.close()
        print("Table 'documents' is ready.")
    except Exception as e:
        print("Error creating documents table:", e)

def store_document(conn, url, text):
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO documents (url, text) VALUES (%s, %s) RETURNING id
        """, (url, text))
        document_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return document_id
    except Exception as e:
        print("Error storing document:", e)
        return None

def store_embeddings(conn, document_id, embeddings):
    try:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE documents SET embeddings = %s WHERE id = %s
        """, (embeddings, document_id))
        conn.commit()
        cursor.close()
        print(f"Stored embeddings for document ID {document_id}")
    except Exception as e:
        print("Error storing embeddings:", e)

def preprocess_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator='\n')
    return text
