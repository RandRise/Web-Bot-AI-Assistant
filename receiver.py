import json
import threading
import rabbitmq_service
from rag_model import rag_model_main
from web_crawler import crawl_website
from rabbitmq_service import RabbitMQService


def process_training_message(ch, method, properties, body):
    try:
        body_str = body.decode('utf-8')
        rawMessage = json.loads(body_str)
        message = json.loads(rawMessage)

        if isinstance(message, dict) and 'id' in message and 'domain' in message:
            bot_id = message['id']  # Convert id to integer if necessary
            domain = message['domain']
            print(
                f"Received training request for bot_id: {bot_id}, domain: {domain}")

            crawl_website(bot_id, url=domain, max_depth=2)

            response_message = {
                'bot_id': bot_id,
                'status': 'Active',
                'message': 'Training process completed. Your Web-bot is Ready!'
            }
            rabbitmq_service = RabbitMQService()
            rabbitmq_service.connect()
            rabbitmq_service.send_message(
                'training_response', json.dumps(response_message))
            rabbitmq_service.close()

        else:
            print("Message does not contain required fields: 'id' and 'domain'")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except TypeError as e:
        print(f"Type error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def process_message_completion_request(ch, method, properties, body):
    try:
        message = json.loads(body)
        question = message.get('question')
        correlation_id = message.get('correlationId')
        bot_id = message.get('bot_id')  # Extract bot_id from the message
        print("BotID",bot_id)
        # Get the replyTo field from the message
        reply_to = message.get('replyTo', 'gpt_response_queue')
        print ("Message", message)
        print(
            f"Received message: Question: {question}, Correlation ID: {correlation_id}")

        # Call the RAG model main function with the question
        answer = rag_model_main(question, bot_id)

        # Ensure answer is not None
        if answer is None:
            answer = "Answer not found."

        # Send the response back to the response queue specified in replyTo
        response = {
            "question": question,
            "answer": answer,
            "correlationId": correlation_id
        }

        rabbitmq_service = RabbitMQService()
        rabbitmq_service.connect()
        rabbitmq_service.send_message(reply_to, json.dumps(response))
        rabbitmq_service.close()

    except Exception as e:
        print(f"Error processing message: {e}")


def start_consuming(queue, callback):
    rabbitmq_service = RabbitMQService()
    rabbitmq_service.connect()
    rabbitmq_service.receive_message(queue, callback)
    rabbitmq_service.channel.start_consuming()


def main():
    try:
        # Start separate threads for each queue
        training_thread = threading.Thread(target=start_consuming, args=(
            'training_request', process_training_message))
        message_completion_thread = threading.Thread(target=start_consuming, args=(
            'message_completion_request', process_message_completion_request))

        training_thread.start()
        message_completion_thread.start()

        training_thread.join()
        message_completion_thread.join()

    except KeyboardInterrupt:
        print('Interrupted')
    finally:
        rabbitmq_service.close()


if __name__ == "__main__":
    main()
