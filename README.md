# Jamiiz AI Demo Lab

Custom AI assistants trained on your business content — three demos, one backend.

**Built with:** FastAPI · LangChain · LangGraph · Pinecone · OpenAI

---

## The Three Demos

| Demo | What it does | Sales message |
|------|-------------|---------------|
| **Document Assistant** | Upload any document (PDF, DOCX, TXT) and ask questions about it | "Imagine your team asking questions across grants, policies, and SOPs instead of searching manually" |
| **Website Assistant** | Answers questions about Jamiiz AI using the knowledge base | "Imagine this on your website capturing leads and answering customer questions 24/7" |
| **Guest Assistant** | Handles property/Airbnb guest questions automatically | "Imagine your guests getting instant answers without you replying to the same messages every day" |

All three share one backend. Adding a new assistant is as simple as adding a prompt and a knowledge base.

---

## Project Structure

```
ai-demos/
├── backend/
│   ├── app/
│   │   ├── main.py                        # FastAPI entry point
│   │   ├── core/
│   │   │   ├── config.py                  # Settings (reads from .env)
│   │   │   └── logging.py
│   │   ├── api/
│   │   │   ├── routes_chat.py             # POST /chat
│   │   │   ├── routes_documents.py        # POST /documents/upload
│   │   │   └── routes_leads.py            # POST /leads
│   │   ├── services/
│   │   │   ├── pinecone_service.py        # One index, namespace per assistant
│   │   │   ├── llm_service.py             # OpenAI chat + prompt loader
│   │   │   ├── rag_service.py             # Retrieve + format context
│   │   │   ├── document_ingestion_service.py  # File → chunks → embeddings → Pinecone
│   │   │   └── lead_service.py            # SQLite: leads + Q&A log
│   │   ├── graphs/
│   │   │   └── document_graph.py          # LangGraph: classify → retrieve → generate → check
│   │   ├── schemas/
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   └── leads.py
│   │   └── assistants/
│   │       ├── document/prompt.md + config.yaml
│   │       ├── website/prompt.md + config.yaml
│   │       └── property/prompt.md + config.yaml
│   ├── pyproject.toml
│   ├── .env.example
│   └── start.sh
└── knowledge/
    ├── jamiiz/          # Jamiiz AI company content
    ├── property/        # Property/guest content
    └── nonprofit/       # Sample NGO documents
```

---

## Getting Started

### 1. Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- OpenAI API key
- Pinecone API key (free tier works for demos)

### 2. Install dependencies

```bash
cd backend

# With uv (recommended — same as a-new-uganda repo):
uv sync

# Or with pip:
pip install -e ".[dev]"
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=jamiiz-ai-demo
```

Pinecone will auto-create the index on first startup. LangSmith tracing is optional but recommended for debugging.

### 4. Run the server

```bash
bash start.sh
# or directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit **http://localhost:8000/docs** for the interactive API explorer.

---

## API Reference

### Chat

```
POST /chat
```

```json
{
  "message": "What are the eligibility requirements?",
  "assistant_type": "document",
  "session_id": "abc-123",
  "history": []
}
```

`assistant_type` is one of `"document"`, `"website"`, `"property"`.

Response includes `answer`, `sources`, `confidence`, `intent`, and `suggest_booking`.

---

### Upload a Document

```
POST /documents/upload
Content-Type: multipart/form-data

file=<your-file>
namespace=document-demo
```

Supported formats: PDF, DOCX, TXT, MD. Max 20 MB.

The document is chunked, embedded, and stored in Pinecone under the given namespace. After upload, you can query it immediately via `/chat`.

---

### Ingest Text Directly

```
POST /documents/text
```

```json
{
  "text": "Check-in is at 3pm. Wi-Fi password is welcome2024.",
  "namespace": "property-demo",
  "source_label": "house-manual"
}
```

Useful for ingesting website content or property guides without a file.

---

### Capture a Lead

```
POST /leads
```

```json
{
  "email": "prospect@company.com",
  "name": "Jane Smith",
  "business": "Property management company",
  "pain_point": "Answering the same guest questions every day",
  "hours_saved": "5-10 hours/week",
  "assistant": "property",
  "session_id": "abc-123"
}
```

Stored in `data/leads.db` (SQLite). Every Q&A pair is also logged for product intelligence.

---

## Pinecone Namespaces

One Pinecone index, three namespaces — clean separation per assistant:

| Assistant | Namespace | Content |
|-----------|-----------|---------|
| Website | `jamiiz-website` | Jamiiz AI company content, services, FAQs |
| Property | `property-demo` | House rules, check-in, local guide |
| Document | `document-demo` | User-uploaded documents |

To ingest the starter knowledge base:

```bash
cd backend
python3 -c "
from app.core.config import get_settings
from app.services.document_ingestion_service import get_ingestion_service
from pathlib import Path

s = get_settings()
ing = get_ingestion_service()

# Ingest Jamiiz knowledge base
ing.ingest_directory(Path('../knowledge/jamiiz'), namespace=s.pinecone_ns_website)

# Ingest property content
ing.ingest_directory(Path('../knowledge/property'), namespace=s.pinecone_ns_property)

# Ingest sample nonprofit docs
ing.ingest_directory(Path('../knowledge/nonprofit'), namespace=s.pinecone_ns_document)
print('Done.')
"
```

---

## LangGraph — Document Assistant Flow

The Document Assistant uses a LangGraph pipeline for multi-step reasoning:

```
START
  → classify_intent     (summarise / extract / question / draft / evaluate)
  → retrieve_context    (Pinecone similarity search, k=5 or 8 for summaries)
  → generate_answer     (GPT-4o-mini with intent-specific instructions)
  → check_confidence    (flags low-confidence answers)
  → END
```

The Website and Property assistants use a simpler RAG → LLM chain (no graph needed for Q&A).

---

## Adding a New Assistant

1. Create `backend/app/assistants/<name>/prompt.md` with the system prompt
2. Create `backend/app/assistants/<name>/config.yaml` with namespace and settings
3. Add the namespace to `.env` and `config.py`
4. Ingest your knowledge base content into the new namespace
5. The `/chat` endpoint will route to it automatically

---

## Demo Script (5 minutes)

1. **Document Assistant** — upload a grant document, ask "Does this grant fit our organization?" and "Draft a problem statement."
2. **Website Assistant** — ask "What does Jamiiz AI do?" and "Can you help a nonprofit?"
3. **Property Assistant** — ask "What time is check-in?" and "The AC isn't working, what should I do?"
4. Show the lead capture: after a few exchanges the assistant suggests booking a Free AI Workflow Review.
5. Close: "We build this for your business — trained on your documents, your workflows, your voice."

---

## Deployment

For demos, the simplest setup is:

- **Backend**: [Render](https://render.com) or [Railway](https://railway.app) (free tier sufficient)
- **Frontend**: Vercel or Hostinger

Set your environment variables in the platform's dashboard. The server starts with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

---

## Roadmap

- [ ] Frontend — React chat widget + demo pages
- [ ] NGO Funding Assistant — LangGraph with grant discovery tools
- [ ] Lead dashboard — view captured leads in the browser
- [ ] Streaming responses — token-by-token output for better UX
- [ ] Multi-tenant namespacing — per-client document isolation
