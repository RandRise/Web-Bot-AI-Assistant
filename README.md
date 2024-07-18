# Web-Bot AI Assistant 

This project is a RAG (Retrieval-Augmented Generation) model implementation that interacts with RabbitMQ for message processing. The project consists of training and completion request processing using a web crawler and OpenAI's API for embedding and generating responses.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.8+
- RabbitMQ
- PostgreSQL
- pgvector extension

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/Web-Bot-AI-Assistant.git
    cd Web-Bot-AI-Assistant
    ```
2. Create a virtual environment and activate it:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1. Copy the `.env.example` file to `.env` and update the environment variables:

    ```bash
    cp .env.example .env
    ```

    - Update the `OPENAI_API_KEY` with your OpenAI API key.
    - Update the PostgreSQL database connection details.

### Running the Application

Start the server:

```bash
python receiver.py
