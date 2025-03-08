# RAG-Based Research Paper Assistant

A FastAPI application that uses Retrieval-Augmented Generation (RAG) to assist with research paper analysis and queries.

## Features

- Upload and process research papers (PDF)
- Index documents using Pinecone vector database
- Query the documents with natural language
- Get RAG-enhanced responses with source citations

## Local Development

### Prerequisites

- Python 3.9+
- Pinecone API Key
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/RAG-Based-Research-Paper-Assistant.git
   cd RAG-Based-Research-Paper-Assistant
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following content:
   ```
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=rag-based-research-paper-assistant-v2
   PINECONE_ENVIRONMENT=us-east-1
   DATABASE_URL=sqlite:///./test.db
   SECRET_KEY=your-secret-key-here
   ```

5. Run the application:
   ```
   python run.py
   ```

The API will be available at `http://localhost:8000`.

## Deployment on Render

This repository is configured for easy deployment on Render.

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add the following environment variables:
   - `PINECONE_API_KEY` (mark as secret)
   - `PINECONE_INDEX_NAME`: rag-based-research-paper-assistant-v2
   - `PINECONE_ENVIRONMENT`: us-east-1
   - `DATABASE_URL`: sqlite:///./prod.db
   - `SECRET_KEY`: (generate a random string)

## API Documentation

Once deployed, you can access the API documentation at:
- `/docs` - Swagger UI
- `/redoc` - ReDoc UI

## License

[MIT License](LICENSE)