# Jamiiz AI Demo Lab

Custom AI assistants trained on real business content — four demos, one backend, one frontend.

**Built with:** FastAPI · LangChain · LangGraph · Pinecone · OpenAI · React (Vite)

---

## The Four Demos

| Demo | Assistant Name | What it does |
|------|---------------|--------------|
| **Jamiiz Assistant** | `website` | Answers questions about Jamiiz AI services, pricing, and use cases — and captures leads |
| **Asante Guest Assistant** | `property` | Handles Asante Stays guest questions: check-in, house rules, amenities, pricing |
| **Document Assistant** | `document` | Upload any document (PDF, DOCX, TXT, MD) and ask questions about it |
| **Smile Again Assistant** | `nonprofit` | Answers questions about Smile Again Families programs, sponsorships, impact, and grants |

All four share one backend and one Pinecone index. Adding a new assistant takes hours, not months.

---

## Project Structure

```
ai-demos/
├── backend/
│   ├── app/
│   │   ├── main.py                            # FastAPI entry point + LangSmith tracing
│   │   ├── core/
│   │   │   ├── config.py                      # Settings (reads from .env)
│   │   │   └── logging.py
│   │   ├── api/
│   │   │   ├── routes_chat.py                 # POST /chat
│   │   │   ├── routes_documents.py            # POST /documents/upload, /documents/text
│   │   │   └── routes_leads.py                # POST /leads
│   │   ├── services/
│   │   │   ├── pinecone_service.py            # One index, namespace per assistant
│   │   │   ├── llm_service.py                 # OpenAI chat + prompt loader
│   │   │   ├── rag_service.py                 # Retrieve + format context
│   │   │   ├── document_ingestion_service.py  # File → chunks → embeddings → Pinecone
│   │   │   └── lead_service.py                # SQLite: leads + Q&A log
│   │   ├── graphs/
│   │   │   └── document_graph.py              # LangGraph: classify → retrieve → generate → check
│   │   ├── schemas/
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   └── leads.py
│   │   └── assistants/
│   │       ├── document/prompt.md + config.yaml
│   │       ├── website/prompt.md + config.yaml
│   │       ├── property/prompt.md + config.yaml
│   │       └── nonprofit/prompt.md + config.yaml
│   ├── ingest.py                              # CLI ingestion script (see below)
│   ├── pyproject.toml
│   ├── .env.example
│   └── start.sh
├── frontend/
│   ├── public/
│   │   └── favicon.png                        # Jamiiz J icon
│   ├── src/
│   │   ├── App.jsx                            # Main layout, demo tabs, lead modal
│   │   ├── App.css                            # Jamiiz brand: navy #0e2340, orange #e07b18
│   │   ├── index.css                          # Inter font, global reset
│   │   ├── api.js                             # sendMessage, uploadDocument, submitLead
│   │   └── components/
│   │       ├── ChatWidget.jsx                 # Chat UI with suggestions + typing indicator
│   │       ├── FileUpload.jsx                 # Drag & drop file upload for Document tab
│   │       └── LeadCaptureForm.jsx            # Lead capture modal
│   ├── index.html
│   ├── vite.config.js                         # Proxy /chat, /documents, /leads → :8000
│   └── package.json
└── knowledge/
    ├── jamiiz/          # Jamiiz AI company content, services, FAQs
    ├── property/        # Asante Stays: amenities, pricing, house rules, local guide
    └── nonprofit/       # Smile Again Families: programs, impact, donor FAQ, grant profile
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20.17+ and npm
- [uv](https://github.com/astral-sh/uv) (recommended)
- OpenAI API key
- Pinecone API key (free tier works)

---

### Backend

#### 1. Install dependencies

```bash
cd backend
uv sync
```

#### 2. Configure environment

```bash
cp .env.example .env
```

Fill in your keys:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=jamiiz-ai-demo

PINECONE_NS_WEBSITE=jamiiz-website
PINECONE_NS_PROPERTY=property-demo
PINECONE_NS_DOCUMENT=document-demo
PINECONE_NS_NONPROFIT=nonprofit-demo

# Optional but recommended
LANGSMITH_API_KEY=ls__...
LANGCHAIN_PROJECT=jamiiz-ai-demos
```

#### 3. Ingest knowledge bases

```bash
cd backend

# Ingest all four namespaces
uv run python3 ingest.py

# Or ingest individually
uv run python3 ingest.py --jamiiz       # Jamiiz AI website content
uv run python3 ingest.py --property     # Asante Stays property content
uv run python3 ingest.py --smile        # Smile Again Families nonprofit content

# Re-ingest cleanly (clears existing vectors first)
uv run python3 ingest.py --clear

# Clear only the document-demo namespace (user uploads)
uv run python3 ingest.py --clear-document
```

Chunk IDs are deterministic (MD5 hash of filename + index), so running ingest twice is safe — it overwrites, never duplicates.

#### 4. Start the backend

```bash
cd backend
bash start.sh
# or directly:
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at **http://localhost:8000/docs**

---

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at **http://localhost:3000** — Vite proxies all `/chat`, `/documents`, `/leads` calls to the backend on port 8000.

---

## API Reference

### POST /chat

```json
{
  "message": "What programs does Smile Again run?",
  "assistant_type": "nonprofit",
  "session_id": "demo-abc123",
  "history": []
}
```

`assistant_type` is one of: `"website"` · `"property"` · `"document"` · `"nonprofit"`

Response:

```json
{
  "answer": "Smile Again runs six core programs...",
  "sources": ["programs.md"],
  "confidence": 0.91,
  "intent": "question",
  "suggest_booking": false
}
```

---

### POST /documents/upload

```
Content-Type: multipart/form-data

file=<your-file>
namespace=document-demo
```

Supported formats: PDF, DOCX, TXT, MD. Max 20 MB. The document is chunked, embedded with `text-embedding-3-small`, and stored in Pinecone. Ready to query immediately.

---

### POST /documents/text

```json
{
  "text": "Check-in is at 3pm. Wi-Fi password is welcome2024.",
  "namespace": "property-demo",
  "source_label": "house-manual"
}
```

---

### POST /leads

```json
{
  "email": "prospect@company.com",
  "name": "Jane Smith",
  "business": "Property management company",
  "pain_point": "Answering the same guest questions every day",
  "assistant": "property",
  "session_id": "demo-abc123"
}
```

Stored in `data/leads.db` (SQLite). Every Q&A exchange is also logged for product intelligence.

---

## Pinecone Namespaces

One index, four namespaces:

| Assistant | Namespace | Content |
|-----------|-----------|---------|
| Jamiiz Assistant | `jamiiz-website` | Services, pricing, FAQs, use cases |
| Asante Guest Assistant | `property-demo` | Amenities, check-in, house rules, pricing |
| Document Assistant | `document-demo` | User-uploaded documents (runtime) |
| Smile Again Assistant | `nonprofit-demo` | Programs, impact data, donor FAQ, grant profile |

---

## LangGraph — Document Assistant Flow

The Document Assistant uses a multi-step LangGraph pipeline:

```
START
  → classify_intent     (summarise / extract / question / draft / evaluate)
  → retrieve_context    (Pinecone similarity search, k=5 or 8 for summaries)
  → generate_answer     (GPT-4o-mini with intent-specific instructions)
  → check_confidence    (flags low-confidence answers)
  → END
```

The other three assistants use a simpler RAG → LLM chain — no graph needed for conversational Q&A.

---

## Adding a New Assistant

1. Create `backend/app/assistants/<name>/prompt.md` — system prompt defining personality and scope
2. Create `backend/app/assistants/<name>/config.yaml` — namespace and model settings
3. Add `PINECONE_NS_<NAME>=<namespace>` to `.env` and `config.py`
4. Add the assistant type to the `Literal` in `backend/app/schemas/chat.py`
5. Add the namespace mapping in `namespace_for()` in `config.py`
6. Add a knowledge base folder under `knowledge/<name>/` and run `ingest.py`
7. Add the demo entry to `DEMOS` array in `frontend/src/App.jsx`

---

## Demo Script (5 minutes)

1. **Jamiiz Assistant** — "What does Jamiiz AI do?" / "How much does it cost?" / "Can you help a nonprofit?"
2. **Asante Guest Assistant** — "What time is check-in?" / "What are the house rules?" / "Tell me about the studio apartment."
3. **Document Assistant** — upload a grant PDF, ask "Does this grant fit our organization?" and "Draft a problem statement."
4. **Smile Again Assistant** — "What programs does Smile Again run?" / "How can I sponsor a girl's education?" / "What is the impact so far?"
5. After 3+ exchanges, the lead capture modal triggers — show how prospects are captured automatically.

---

## Deployment

| Layer | Platform | Notes |
|-------|----------|-------|
| Backend | [Render](https://render.com) or [Railway](https://railway.app) | Free tier sufficient for demos |
| Frontend | [Vercel](https://vercel.com) or Hostinger | Static build: `npm run build` |

Set all `.env` variables in the platform dashboard. Backend starts with:

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Update `ALLOWED_ORIGINS` in `.env` to include your production frontend URL.

---

## Roadmap

- [x] FastAPI backend with four assistants
- [x] LangGraph pipeline for Document Assistant
- [x] Pinecone RAG with deterministic chunk IDs
- [x] LangSmith tracing
- [x] React frontend (Vite) with Jamiiz branding
- [x] Lead capture modal + SQLite storage
- [x] Smile Again nonprofit assistant
- [ ] Streaming responses — token-by-token output
- [ ] Lead dashboard — view captured leads in the browser
- [ ] Tavily search integration — live web search for Jamiiz assistant
- [ ] Multi-tenant namespacing — per-client document isolation
- [ ] NGO Funding Assistant — LangGraph with grant discovery tools
