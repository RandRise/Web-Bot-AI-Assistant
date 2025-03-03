import numpy as np
import openai
import os
import tiktoken
from dotenv import load_dotenv
from db_connection import connect_to_database

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')


def fetch_documents(conn, question_embedding, bot_id, similarity_threshold=0.7):
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
            LIMIT 3
        """, (question_embedding.tolist(),
              bot_id,
              question_embedding.tolist(),
              similarity_threshold))

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


def count_tokens(text):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    return len(tokens)


def trim_messages_to_fit_limit(messages, max_tokens):
    total_tokens = sum(count_tokens(
        message['content']) for message in messages)
    while total_tokens > max_tokens:
        total_tokens -= count_tokens(messages[0]['content'])
        messages.pop(0)
    return messages


def generate_answer(question, relevant_documents, lastMessages):

    context = "\n\n".join(
        [doc[2] for doc in relevant_documents]) if relevant_documents else ""

    messages = [

        {"role": "system", "content": "You are a helpful assistant for the website."}]

    for lastMsg in lastMessages:
        
        role = 'user' if lastMsg.get('type') == 1 else 'system'
        
        messages.append({"role": role, "content": lastMsg.get('content')})

    messages = trim_messages_to_fit_limit(messages, max_tokens=8000)

    messages.append({"role": "user", "content": f"Use the relevant information provided to answer the Question below. Respond in the same language as the Question.English is the desired language unless the question was asked in another language. If you don't know the answer, try to answer based on old messages. If you don't know the answer, don't improvise with random answers.\n\nRelevant Information:\n{context}\n\nQuestion: {question}\nAnswer:"})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
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


def rag_model_main(user_question, bot_id, lastMessages):
    question = user_question

    conn = connect_to_database()
    if not conn:
        return "Failed to connect to the database."

    question_embedding = calculate_embedding(question)
    if question_embedding is None:
        return "Error generating question embedding."

    documents = fetch_documents(conn, question_embedding, bot_id)

    answer = generate_answer(question, documents, lastMessages)

    output = format_output(question, answer)

    conn.close()
    return answer
