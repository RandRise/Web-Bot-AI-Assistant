import numpy as np
from db_connection import connect_to_database
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

def fetch_documents(conn, question_embedding, bot_id, similarity_threshold=0.75):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                id, url, text, embeddings,
                1 - cosine_distance(embeddings, %s::VECTOR) AS similarity
            FROM
                documents
            WHERE
                bot_id = %s
                AND embeddings IS NOT NULL
                AND 1 - cosine_distance(embeddings, %s::VECTOR) > %s
            ORDER BY
                similarity DESC
        """, (question_embedding.tolist(), bot_id, question_embedding.tolist(), similarity_threshold))

        documents = cursor.fetchall()
        cursor.close()
        return documents
    except Exception as e:
        print("Error fetching documents:", e)
        return []

def calculate_embedding(text):
    try:
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        embeddings = response['data'][0]['embedding']

        return np.array(embeddings)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def generate_answer(question, relevant_documents):
    context = "\n\n".join([doc[2] for doc in relevant_documents]) if relevant_documents else ""
    messages = [
        {"role": "system", "content": "You are a helpful assistant for the website."},
        {"role": "user", "content": f"Question: {question}\n\nContext: {context}\n\nAnswer:"}
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("Error generating answer:", e)
        return "Could not generate an answer at this time."

def format_output(question, answer):
    output = (
        "\n----------------------------------------\n"
        "Prompt:\n"
        f"{question}\n"
        "----------------------------------------\n"
    )
    output += (
        "Response:\n"
        f"{answer}\n"
        "----------------------------------------\n"
    )
    return output

def rag_model_main(user_question, bot_id):
    question = user_question

    conn = connect_to_database()
    if not conn:
        return "Failed to connect to the database."

    question_embedding = calculate_embedding(question)
    if question_embedding is None:
        return "Error generating question embedding."

    documents = fetch_documents(conn, question_embedding, bot_id)
    if not documents:
        print("No documents found in the database.")
        return "No documents found in the database."

    answer = generate_answer(question, documents)

    output = format_output(question, answer)
    print(output)

    conn.close()
    return answer
