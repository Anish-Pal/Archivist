# Archivist — Enterprise RAG Assistant

> Turn scattered enterprise documents into a searchable, conversational knowledge base — with answers grounded in retrieved sources and citations you can trace back to the original documents.

Archivist is a multi-user Retrieval-Augmented Generation (RAG) application that lets users upload their own documents and ask questions about them in plain language. The system combines dense vector retrieval, sparse keyword retrieval, Reciprocal Rank Fusion (RRF), cross-encoder reranking, query rewriting, conversational history, and citation validation to produce source-grounded answers.

Built with a focus on practical backend engineering, retrieval quality, authentication, multi-user data isolation, document management, and a custom web interface.

---

## Table of Contents

- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Setup and Installation](#setup-and-installation)
- [Linting](#linting)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Security and Multi-Tenancy](#security-and-multi-tenancy)
- [Deployment](#deployment)
- [Known Limitations](#known-limitations)
- [Future Work](#future-work)
- [License](#license)

---

## Key Features

### Retrieval and Generation

- Multi-format document ingestion for PDF, TXT, and CSV files
- SHA-256 file hashing for per-user duplicate detection
- Recursive character-based text chunking
- Dense vector retrieval using ChromaDB
- Sparse keyword retrieval using BM25
- Hybrid retrieval using Reciprocal Rank Fusion (RRF)
- Cross-encoder reranking with `BAAI/bge-reranker-base`
- Query rewriting for conversational follow-up questions
- Prompt-enforced grounding using retrieved document context
- Citation validation against the actual retrieved chunks before citations are returned to the user
- LLM answer generation through the Groq API

### Conversations

- Persistent PostgreSQL-backed conversation history
- Resume previous conversations
- Automatic conversation title generation from the first user message
- User and assistant messages stored in the database
- Citations persisted alongside assistant messages
- Lazy conversation creation — a new database conversation is created only when the user sends the first message

### Authentication and Multi-Tenancy

- User signup and login
- Password hashing with `passlib` and `bcrypt`
- Session-based authentication using HTTP cookies
- Expiring user sessions
- Logout with server-side session invalidation
- Per-user document isolation
- Ownership checks for documents and conversations
- ChromaDB retrieval filtered by `user_id`
- Per-user BM25 retrieval state
- Per-user duplicate detection
- Resources belonging to another user are not exposed through ownership checks

### Document and Conversation Management

- Upload documents
- List uploaded documents
- Delete documents
- Delete associated ChromaDB chunks during document deletion
- Delete uploaded files from the filesystem
- Rebuild the affected user's BM25 retrieval state after document deletion
- Create, list, resume, and delete conversations

### Interface

- Custom web interface built without a UI framework
- Chat interface
- Login page
- Signup page
- Document sidebar
- Conversation sidebar
- Typing indicator
- Active conversation highlighting
- Resume-last-conversation behavior
- Document and conversation deletion
- Dark/light theme toggle
- Theme preference persisted with `localStorage`
- Responsive UI styling

---

## How It Works

### Document ingestion

1. The authenticated user uploads a document.
2. The file is stored with a unique server-side filename.
3. A SHA-256 hash is calculated for duplicate detection.
4. A PostgreSQL document record is created.
5. Text is extracted using the appropriate document loader.
6. Extracted text is split into smaller chunks.
7. Metadata such as `user_id`, `document_id`, filename, and file hash is attached to the chunks.
8. Chunks are embedded using `BAAI/bge-small-en-v1.5`.
9. Embeddings and metadata are stored in ChromaDB.
10. The user's BM25 retrieval index is rebuilt.

### Question answering

1. The user sends a question.
2. Previous conversation history is loaded from PostgreSQL.
3. The system determines whether the question needs query rewriting.
4. If required, the question is rewritten into a standalone query.
5. Dense vector retrieval searches the user's ChromaDB chunks.
6. BM25 searches the user's sparse retrieval index.
7. Results from both retrieval methods are combined using Reciprocal Rank Fusion.
8. The fused candidates are passed through the BGE cross-encoder reranker.
9. The highest-ranked chunks are selected as the final context.
10. The context is provided to the LLM.
11. The generated answer and citation references are validated against the retrieved chunks.
12. The answer, user message, and validated citations are stored in PostgreSQL.

---

## Architecture

### 1. Ingestion Pipeline

```text
                    Upload
                       │
                       ▼
          Create PostgreSQL document
             record for the user
                       │
                       ▼
              Calculate SHA-256
                       │
                       ▼
          Already indexed for user?
                  │          │
                 YES         NO
                  │          │
                  ▼          ▼
                Skip      Extract text
                              │
                              ▼
                           Chunk text
                              │
                              ▼
                     Attach metadata
                              │
                              ▼
                    Generate embeddings
                              │
                              ▼
                         ChromaDB
                              │
                              ▼
                    Rebuild user's BM25
                         index/cache
```

### 2. Query Pipeline

```text
                  User question
                       │
                       ▼
              Conversation history
                       │
                       ▼
             Query rewriting needed?
                    │       │
                   NO      YES
                    │       │
                    │       ▼
                    │   Rewrite query
                    │       │
                    └───┬───┘
                        ▼
                Hybrid Retrieval
                  /           \
                 ▼             ▼
          Vector Search      BM25
            ChromaDB       per-user index
                 \             /
                  ▼           ▼
                Reciprocal Rank
                    Fusion
                       │
                       ▼
                Candidate chunks
                       │
                       ▼
              Cross-encoder reranker
                       │
                       ▼
                 Final top-k
                       │
                       ▼
                Build numbered
                   context
                       │
                       ▼
                      LLM
                       │
                       ▼
              Answer + citations
                       │
                       ▼
              Validate citations
                       │
                       ▼
                 Store message
                    + citations
```

### 3. Multi-User Isolation

```text
                    PostgreSQL
              ┌───────────────────┐
              │ Users             │
              │ Documents         │
              │ Conversations     │
              │ Messages          │
              │ UserSessions      │
              └─────────┬─────────┘
                        │
                        │ ownership
                        ▼
              ┌───────────────────┐
              │     ChromaDB      │
              │                   │
              │ chunks + metadata │
              │ user_id           │
              │ document_id       │
              │ source            │
              └─────────┬─────────┘
                        │
                 user_id filter
                        │
                        ▼
                 Current user's
                  retrieval set
```

Retrieval is scoped to the authenticated user before results are fused or reranked. Database ownership checks are also applied to user-owned resources such as documents and conversations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| Server | Uvicorn |
| Templates | Jinja2 |
| Database ORM | SQLAlchemy |
| Relational database | PostgreSQL |
| Vector store | ChromaDB |
| Dense embeddings | `BAAI/bge-small-en-v1.5` |
| Sparse retrieval | `rank-bm25` / BM25Okapi |
| Reranker | `BAAI/bge-reranker-base` |
| RAG framework | LangChain |
| Document parsing | LangChain community loaders / PyPDF |
| LLM inference | Groq API |
| Authentication | Session cookies + Passlib/Bcrypt |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Model runtime | Sentence Transformers / PyTorch |

---

## Project Structure

```text
Enterprise RAG Assistant/
│
|
├── requirements.txt
├── requirements-dev.txt
├── .flake8
├── .gitignore
├── .dockerignore
├── .env.example
├── Dockerfile
│
├── docker/
│   ├── entrypoint.sh
│   └── bootstrap_db.py
│
├── deploy/
│   └── aws/
│       ├── bootstrap.sh
│       ├── docker-compose.yml
│       ├── nginx.conf
│       └── .env.example
│
├── api/
│   ├── __init__.py
│   ├── dependencies.py
│   ├── main.py
│   └── schemas.py
│
├── auth/
│   ├── __init__.py
│   ├── dependencies.py
│   ├── schemas.py
│   ├── security.py
│   └── session.py
│
├── database/
│   ├── __init__.py
│   ├── crud.py
│   ├── database.py
│   ├── init_db.py
│   └── models.py
│
├── src/
│   ├── config.py
│   ├── rag_initializer.py
│   ├── rag_pipeline.py
│   ├── ingestion_pipeline.py
│   ├── loaders.py
│   ├── splitter.py
│   ├── metadata.py
│   ├── hashing.py
│   ├── embedder.py
│   ├── vector_store.py
│   ├── chunk_store.py
│   ├── bm25_retriever.py
│   ├── hybrid_retriever.py
│   ├── reranker.py
│   ├── context_builder.py
│   ├── citations.py
│   ├── llm.py
│   ├── query_rewriter.py
│   └── query_detector.py
│
├── templates/
│   ├── chat.html
│   ├── login.html
│   └── signup.html
│
├── static/
│   ├── css/
│   │   ├── chat.css
│   │   ├── auth.css
│   │   └── signup.css
│   │
│   └── Js/
│       ├── chat.js
│       ├── login.js
│       └── signup.js
│
├── data/
│   └── # Uploaded documents — gitignored
│
└── chroma_db/
    └── # Local ChromaDB storage — gitignored
```

> The local project directory can be named `Enterprise RAG Assistant`; the GitHub repository is named `Archivist`.

---

## Screenshots

### Login

![Archivist Login](screenshots/login.png)

### Create Account

![Archivist Signup](screenshots/signup.png)

### Chat Interface

![Archivist Chat](screenshots/chat.png)

---

## Setup and Installation

### Prerequisites

- Python 3.10+
- PostgreSQL
- Groq API key
- Hugging Face account/token if required by the model downloads or your configuration

### 1. Clone the repository

```bash
git clone <https://github.com/Anish-Pal/Archivist.git>
cd Archivist
```

> The GitHub repository is named `Archivist`, even though the local development folder may use the name `Enterprise RAG Assistant`.

### 2. Create a virtual environment

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
DB_URL=postgresql://user:password@localhost:5432/archivist
```

See [`.env.example`](.env.example) for the full list, including the optional
`DATA_FOLDER`, `CHROMA_DB_PATH` and `COOKIE_SECURE` overrides.

Never commit `.env` or API keys to GitHub.

### 5. Start PostgreSQL

Create the PostgreSQL database configured in `DB_URL`, then apply the schema:

```bash
python docker/bootstrap_db.py
alembic stamp head
```

For a database that already has an `alembic_version` table, run
`alembic upgrade head` instead.

### 6. Run the application

```bash
uvicorn api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

### Linting

```bash
pip install -r requirements-dev.txt
flake8
```

Configuration lives in [`.flake8`](.flake8). The project's spacing conventions
(`Depends , get_db`, `key = "value"`) are excluded; pyflakes checks, line
length, comparison correctness and whitespace hygiene are enforced.

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Authenticates requests to the Groq API |
| `HF_TOKEN` | Hugging Face authentication when required |
| `DB_URL` | PostgreSQL connection string |
| `DATA_FOLDER` | Upload directory (default `data`) |
| `CHROMA_DB_PATH` | ChromaDB persistence directory (default `chroma_db`) |
| `COOKIE_SECURE` | Set `true` to restrict the session cookie to HTTPS |

Keep credentials in `.env` locally and configure them as environment variables on the hosting platform.

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/signup` | Create a new user account |
| `POST` | `/login` | Authenticate and create a session |
| `POST` | `/logout` | Invalidate the current session |

### Documents

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Upload and index a document |
| `GET` | `/documents` | List the authenticated user's documents |
| `GET` | `/documents/{document_id}` | Get a user's document metadata |
| `DELETE` | `/documents/{document_id}` | Delete a document and its indexed chunks |

### Conversations

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Ask a question and create a conversation when necessary |
| `POST` | `/conversations` | Explicitly create a conversation |
| `GET` | `/conversations` | List the authenticated user's conversations |
| `GET` | `/conversations/{conversation_id}/messages` | Get conversation messages |
| `DELETE` | `/conversations/{conversation_id}` | Delete a conversation |

### Pages

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Application home/API entry point |
| `GET` | `/login` | Login page |
| `GET` | `/signup` | Signup page |
| `GET` | `/chat-page` | Chat interface |

> Keep this API table synchronized with the routes that actually exist in the application.

---

## Security and Multi-Tenancy

Archivist is designed so that user-owned data is isolated throughout the application.

### Authentication

- Passwords are stored as hashes rather than plaintext passwords.
- Login creates a server-side session.
- The session identifier is stored in an HTTP cookie.
- Session records have an expiration time.
- Logout removes the server-side session and deletes the cookie.

### Document isolation

Documents are associated with a `user_id`.

Retrieval uses the authenticated user's identity to restrict the search space:

```text
Authenticated user
       ↓
user_id
       ↓
ChromaDB filter
       +
per-user BM25 index
       ↓
only that user's chunks
```

### Resource ownership

Document and conversation queries include the current user's ID when looking up resources. This prevents users from accessing resources belonging to another account.

---

## Deployment

The app ships as a Docker image, deployed to a single **EC2** instance with
**Neon** as the managed PostgreSQL instance.

### Why this shape

Three properties of the app drive the deployment:

- **Memory.** `bge-reranker-base` and `bge-small-en-v1.5` are loaded in-process
  at startup, so the container needs roughly 2.5–4 GB of RAM. A `t3.medium`
  (4 GB) fits with swap configured as headroom.
- **State.** Uploaded files and the Chroma index live on disk and belong on a
  volume. Chroma persists through SQLite, so this must be **block storage**
  (EBS or a local disk) — SQLite over NFS such as EFS has broken locking and
  will corrupt or hang under concurrent access. This rules out Fargate + EFS.
- **A single process.** Per-user BM25 indexes are held in `app.state` and built
  once during startup, so the app runs with exactly one Uvicorn worker and must
  not be horizontally scaled.

### Files

| Path | Purpose |
|---|---|
| `Dockerfile` | CPU-only Torch, model weights baked into the image, runs as UID 1000 |
| `docker/entrypoint.sh` | Validates secrets, resolves storage, migrates, starts Uvicorn |
| `docker/bootstrap_db.py` | Chooses between schema creation and an incremental Alembic upgrade |
| `deploy/aws/bootstrap.sh` | Provisions a fresh Ubuntu instance end to end |
| `deploy/aws/docker-compose.yml` | Runs the app on loopback with a bind-mounted volume |
| `deploy/aws/nginx.conf` | TLS reverse proxy with upload and timeout limits raised |

### EC2

1. **Create a Neon project** and copy the pooled connection string. Append
   `?sslmode=require`.
2. **Launch the instance** — Ubuntu 24.04, `t3.medium` (4 GB), and a **30 GB**
   root volume. The image is ~3.1 GB and the build needs room for layers; the
   8 GB default runs out of disk.
3. **Security group** — allow inbound 22, 80 and 443 only. The app binds to
   loopback and is never exposed directly.
4. **Point a domain** at the instance's public IP, if you want TLS.
5. **Configure and run:**

   ```bash
   git clone https://github.com/<you>/Archivist.git
   cd Archivist
   cp deploy/aws/.env.example deploy/aws/.env
   # fill in DB_URL and GROQ_API_KEY
   sudo ./deploy/aws/bootstrap.sh example.com
   ```

`bootstrap.sh` installs Docker, nginx and certbot, adds 2 GB of swap, creates
`/srv/archivist/data` owned by UID 1000, builds the image, and issues a
certificate. It is idempotent, so re-running it is safe. Omit the domain to set
everything up without nginx and verify locally against
`http://127.0.0.1:7860/login` first.

Two limits nginx applies by default would break the app, and the supplied
config raises both: `client_max_body_size` (1 MB, so document uploads would
fail as a 413) and `proxy_read_timeout` (60 s, shorter than a cold retrieval
plus reranking plus LLM call).

Updating:

```bash
git pull
sudo docker compose -f deploy/aws/docker-compose.yml up -d --build
```

### Verifying the image locally

```bash
docker build -t archivist .

# /data must be writable by UID 1000.
docker volume create archivist-data
docker run --rm -v archivist-data:/data --user root \
  --entrypoint chown archivist -R 1000:1000 /data

docker run --rm -p 7860:7860 \
  -e DB_URL="postgresql://..." \
  -e GROQ_API_KEY="..." \
  -e COOKIE_SECURE=false \
  -v archivist-data:/data \
  archivist
```

`COOKIE_SECURE=false` is needed only for local testing: the image defaults to
`true`, and a browser will not return a `Secure` cookie over plain HTTP.
Without a writable `/data` the container still starts, but logs a warning and
falls back to ephemeral storage.

### Operational notes

- **Anyone who can reach the app can sign up.** Signup has no email
  verification and every account's questions consume the same Groq quota.
  Restrict access or accept public use deliberately.
- `COOKIE_SECURE=true` is set in the image; nginx terminates TLS and Uvicorn
  runs with `--proxy-headers`, so the client scheme and IP come from the proxy.
- The app runs one worker by design. Do not add `--workers` or place it behind
  an autoscaler.

---

## Known Limitations

- **BM25 rebuild cost:** The affected user's BM25 index is rebuilt after document uploads and deletions. This is reasonable for the current project scale but would benefit from incremental indexing at larger scale.
- **Local file and vector-store coordination:** Document deletion touches PostgreSQL, the filesystem, and ChromaDB separately. A failure between operations could leave partially cleaned-up state. A larger production system would benefit from a more robust cleanup/retry workflow.
- **No email verification:** Signup currently creates accounts without email or OTP verification.
- **Model cold start:** Deployment on limited hosting resources can have noticeable startup latency because embedding and reranker models need to load into memory.
- **Local ChromaDB storage:** The current architecture uses persisted local ChromaDB storage. Production deployment requires persistent storage or a managed/external vector database.
- **Document format scope:** The current interface advertises PDF, TXT, and CSV uploads. Additional formats can be added by extending the loaders, supported extensions, and frontend file input.

---

## Future Work

**Retrieval & Indexing**
- Incremental BM25 index updates
- Semantic or embedding-based chunking
- Markdown/header-aware chunking
- External/managed vector database (e.g., Qdrant) for native multi-tenancy

**Security & Operations**
- Role- or department-level document sharing
- Email/OTP verification
- More robust document cleanup and retry handling
- Background ingestion jobs for large documents
- Rate limiting under LLM API quota exhaustion

**Quality & Observability**
- Retrieval and citation evaluation benchmarks
- Production monitoring and observability
- Streaming LLM responses

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for the full license text.

---

## Project Status

Archivist is currently feature-complete and is ready for final testing, deployment, documentation, and portfolio presentation.
