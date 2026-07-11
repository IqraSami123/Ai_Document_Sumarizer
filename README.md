# AI Document Summarizer

A production-oriented FastAPI application that extracts text from uploaded PDFs and generates concise AI summaries through the OpenAI Responses API.

## Stack

- Python 3.12
- FastAPI and Uvicorn
- Jinja2 server-rendered templates
- Vanilla CSS and JavaScript
- Docker Compose
- PyMuPDF PDF text extraction
- OpenAI Python SDK and Responses API

## Project structure

```text
app/
├── main.py                 # Application factory and middleware
├── config.py               # Environment-backed configuration
├── routes/                 # HTTP route modules
├── services/               # Future business-service modules
├── templates/              # Jinja2 templates
├── static/
│   ├── css/                # Stylesheets
│   └── js/                 # Browser JavaScript
├── utils/                  # Shared helper modules
└── prompts/                # Future AI prompt templates
```

## Run with Docker

1. Optionally copy `.env.example` to `.env` and adjust values.
2. Start the service:

   ```bash
   docker compose up --build
   ```

3. Open <http://localhost:8001>. API documentation is available at <http://localhost:8001/docs>.

## Local development

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Configuration

Configuration is provided through environment variables. See `.env.example` for the available values.

`OPENAI_API_KEY` is required to generate summaries. PDFs must be text-based and no larger than 20 MB.
