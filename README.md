# Agentic RAG Generator

A production-oriented modular monolith built with Python, FastAPI, LangChain,
OpenAI, ChromaDB, `pdfplumber`, Pydantic, and pytest.

The service accepts PDFs at runtime, indexes them into one shared corpus, and
answers questions using only retrieved document text. Questions do not require a
collection ID: every uploaded document is searched.

## Architecture

```text
RAG_Generate_Assesment/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── database.py
│   │       ├── documents.py
│   │       ├── health.py
│   │       └── questions.py
│   ├── application/services/
│   │   ├── database_service.py
│   │   ├── ingestion_service.py
│   │   └── question_service.py
│   ├── domain/
│   │   ├── entities.py
│   │   ├── exceptions.py
│   │   └── ports.py
│   ├── infrastructure/
│   │   ├── config.py
│   │   ├── loaders/pdf_loader.py
│   │   ├── persistence/
│   │   │   ├── chroma_store.py
│   │   │   └── metadata_store.py
│   │   └── providers/
│   │       ├── openai_chat.py
│   │       └── openai_embeddings.py
│   └── schemas/
├── tests/
├── data/                 # Runtime ChromaDB, metadata, and temporary uploads
├── .env.example
├── requirements.txt
└── README.md
```

The API layer owns HTTP concerns. Application services orchestrate use cases.
The domain layer contains entities, ports, and exceptions without vendor
dependencies. Infrastructure implements those ports. This keeps business logic
testable and allows adapters to be replaced.

## RAG flow

1. `POST /api/v1/documents` validates and temporarily stores a PDF.
2. `pdfplumber` extracts non-empty page text.
3. The ingestion service creates overlapping chunks with page metadata.
4. OpenAI embeddings are generated and persisted in ChromaDB.
5. Document metadata is stored in `data/documents.json`.
6. A question is embedded and searched across all ChromaDB collections.
7. Retrieved chunks are passed to a `ChatPromptTemplate`.
8. The chat model may answer only with source-supported facts, basic reasoning,
   arithmetic, date arithmetic, and direct common-sense deductions.
9. The response includes citations with document, filename, page, and score.

If the retrieved text does not support an answer, the exact fallback is:

```text
I cannot find the information you have requested
```

Uploading the same filename or checksum replaces the previous document after
the new vectors have been indexed.

## API

### `GET /health/live`

Returns a liveness response:

```json
{"status": "ok"}
```

### `POST /api/v1/documents`

Upload one PDF as multipart form data:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/documents" `
  -H "accept: application/json" `
  -F "file=@C:\docs\handbook.pdf;type=application/pdf"
```

Response: `201 Created`.

```json
{
  "id": "doc_7f2e6d6ddbb84e12a4f9b1c2c1e4c9f8",
  "filename": "handbook.pdf",
  "content_type": "application/pdf",
  "size_bytes": 248731,
  "page_count": 18,
  "chunk_count": 42,
  "status": "indexed",
  "error": null,
  "created_at": "2026-08-25T05:00:00+00:00",
  "indexed_at": "2026-08-25T05:00:08+00:00"
}
```

### `POST /api/v1/questions`

Ask across all uploaded documents:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/questions" `
  -H "Content-Type: application/json" `
  -d '{\"question\":\"What is the incident escalation process?\"}'
```

Request body:

| Field | Type | Description |
|---|---|---|
| `question` | string | Required, 1-4000 characters |

Example response:

```json
{
  "answer": "The incident escalation process is ...",
  "citations": [
    {
      "document_id": "doc_123",
      "filename": "handbook.pdf",
      "page_number": 14,
      "relevance_score": 0.87
    }
  ]
}
```

### `DELETE /api/v1/database`

Deletes all ChromaDB collections and document metadata. It returns `204 No
Content` and should be protected before deployment outside a trusted
environment.

```powershell
curl.exe -X DELETE "http://127.0.0.1:8000/api/v1/database"
```

Errors use this shape:

```json
{
  "detail": {
    "code": "query_failed",
    "message": "Unable to generate a grounded answer"
  }
}
```

## Configuration

Copy `.env.example` to `.env` and set the secret locally. `.env` is required
for local credentials and must not be committed; `.env.example` is the safe
template that should remain in the repository.

| Variable | Default | Purpose |
|---|---|---|
| `APP_NAME` | `rag-generator` | FastAPI application name |
| `API_PREFIX` | `/api/v1` | API route prefix |
| `OPENAI_API_KEY` | empty | OpenAI credential |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Answer model |
| `CHROMA_PERSIST_DIRECTORY` | `data/chroma` | Vector database path |
| `CHROMA_COLLECTION_NAME` | `rag_documents` | New upload collection |
| `METADATA_FILE` | `data/documents.json` | Metadata file |
| `TEMP_UPLOAD_DIRECTORY` | `data/uploads` | Temporary upload path |
| `MAX_UPLOAD_SIZE_BYTES` | `10485760` | Maximum PDF size |
| `MAX_DOCUMENT_PAGES` | `500` | Maximum PDF pages |
| `CHUNK_SIZE` | `1000` | Chunk target size |
| `CHUNK_OVERLAP` | `150` | Chunk overlap |
| `RETRIEVAL_TOP_K` | `5` | Default result count |
| `RETRIEVAL_SCORE_THRESHOLD` | `0.0` | Minimum relevance score |

## Running in PyCharm on Windows

1. Create/select a Python 3.14 virtual environment.
2. Install dependencies:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
4. Run the application:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```

5. Open `http://127.0.0.1:8000/docs`.

The default host is `127.0.0.1` and the default port is `8000`.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests mock external model calls and cover ingestion, replacement, retrieval,
grounded responses, fallback behavior, persistence, database clearing, and API
contracts.

## Security and operational considerations

- Never commit `.env`, API keys, uploaded files, or `data/`.
- Enforce PDF type, size, page, and chunk limits.
- Keep temporary files server-generated and remove them after processing.
- Treat retrieved text as untrusted input and defend against prompt injection.
- Add authentication, authorization, tenant isolation, rate limiting, and
  structured request IDs before production exposure.
- Use bounded provider retries and surface failures as typed API errors.
