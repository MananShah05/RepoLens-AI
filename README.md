# 🔍 RepoLens AI

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js%2014-000000?style=for-the-badge&logo=nextdotjs)](https://nextjs.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-38B2AC?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-3F70FF?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PC9zdmc+)](https://trychroma.com)
[![Tree-sitter](https://img.shields.io/badge/Tree--sitter-1D232A?style=for-the-badge)](https://tree-sitter.github.io/tree-sitter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **RepoLens AI** is an AI-powered GitHub repository understanding platform. It automates the process of explaining complex codebases, summarizing architectures, generating interactive dependency diagrams, and helping developers onboard in minutes instead of days.

---

## 🌟 Key Features

### 📂 Intelligent Repository Ingestion
*   **Seamless Import:** Provide any public GitHub repository URL to clone and ingest in real-time.
*   **Frictionless Syncing:** Tracks file hashes to perform incremental parsing and avoid redundant indexing.
*   **Respects Filters:** Fully respects `.gitignore` rules and skips binary, vendor, lock, and configuration noise automatically.

### 🌲 AST-Powered Syntax Parsing
*   **Multi-Language Tree-sitter Parsers:** Deep Abstract Syntax Tree (AST) analysis for **Python, JavaScript, TypeScript, Go, Java, C, and C++**.
*   **Symbol Extraction:** Indexes all classes, functions, routes, imports, and exports with precise line and character offsets.
*   **Semantic Chunking:** Splits code intelligently based on functional boundaries (like complete function or class blocks) rather than blind line limits.

### 🧠 Advanced RAG & Vector Search
*   **Hybrid Search Pipeline:** Combines ChromaDB semantic dense retrieval with SQL keyword-based sparse search over symbols and file paths.
*   **OpenRouter Orchestration:** Leverages high-performance LLMs and embedding models (such as `text-embedding-3-small` and advanced chat models) via OpenRouter.
*   **Accurate Citations:** Every AI response is fully grounded in the retrieved code, complete with clickable file path and line number citations.

### 📊 Interactive Visualizations
*   **Interactive File Explorer:** Sleek folder navigation and file hierarchy visualization directly in the browser.
*   **Mermaid-Powered Graphs:** Generates rich, clean system architecture and module dependency diagrams representing the system's runtime and logical structure.

### 🚀 Developer Onboarding Assistant
*   **Setup Checklists:** Automatically generates project-specific setup tasks.
*   **Reading Paths:** Recommends a logical sequential order of files to read to understand the repository structure.
*   **System Map:** Summarizes key entry points, primary API controllers, and expected environment variables.

---

## 🏗️ System Architecture

RepoLens AI uses a highly decoupled, modern RAG architecture:

```mermaid
graph TD
    %% Frontend Layer
    subgraph Frontend [Next.js 14 Web UI]
        UI[App Dashboard]
        Explorer[Interactive File Tree]
        ChatUI[RAG Chat Workspace]
        DiagramCanvas[Mermaid.js Architecture Canvas]
        OnboardingView[Developer Onboarding Checklist]
    end

    %% Backend Layer
    subgraph Backend [FastAPI Application Server]
        API[API Gateway & Router]
        IngestionWorker[Async Ingestion Service]
        ParserService[Tree-Sitter AST Parser]
        IndexerService[Vector Embeddings Service]
        RetrievalEngine[Hybrid Semantic & Lexical Retriever]
        LLMOrchestrator[OpenRouter Prompt Generator]
        DiagramService[Mermaid Graph Generator]
    end

    %% Storage Layer
    subgraph Storage [Persistent Storage & Indexing]
        DB[(PostgreSQL Database - Neon)]
        VectorDB[(ChromaDB Vector Store)]
        DiskStorage[(Local Repository Clones)]
    end

    %% Integrations
    subgraph Remote [External Integrations]
        GitHubAPI[GitHub Repository Clones]
        OpenRouter[OpenRouter API LLM & Embeddings]
    end

    %% Connections
    UI -->|1. Submit GitHub URL| API
    API -->|2. Trigger Async Ingestion| IngestionWorker
    
    IngestionWorker -->|3. Clone Repos| GitHubAPI
    IngestionWorker -->|4. Save Files| DiskStorage
    
    IngestionWorker -->|5. Run AST Extraction| ParserService
    ParserService -->|6. Save Symbols & Files| DB
    
    IngestionWorker -->|7. Embed Code Chunks| IndexerService
    IndexerService -->|8. Generate Embeddings| OpenRouter
    IndexerService -->|9. Persist Vectors| VectorDB

    ChatUI -->|10. Ask Codebase Q&A| API
    API -->|11. Query Context| RetrievalEngine
    RetrievalEngine -->|12. Semantic Fetch| VectorDB
    RetrievalEngine -->|13. Symbol/Lexical Fetch| DB
    
    API -->|14. Orchestrate Prompt| LLMOrchestrator
    LLMOrchestrator -->|15. Generate Answer| OpenRouter
    LLMOrchestrator -->|16. Formatted Response + Citations| ChatUI
    
    API -->|17. Generate Diagrams & Docs| DiagramService
    DiagramService -->|18. Dynamic Diagrams & Checklist| UI
```

---

## ⚡ Recent Optimizations & Benchmarks

RepoLens AI's parsing and ingestion pipeline was recently refactored to handle enterprise-level codebases:

*   **Precompiled AST Queries:** Tree-sitter query patterns are compiled once at module initialization, eliminating compile-on-the-fly AST bottlenecks.
*   **Single-Pass Byte Extraction:** Shifted from text decoding to raw binary (`rb`) file operations, linking line coordinates and byte-offsets directly. Solved character/byte alignment bugs.
*   **PostgreSQL Sanitization:** Integrated deep Unicode `\x00` NUL character sanitization at the database boundary to eliminate transaction rollbacks on binary artifacts.
*   **Performance Benchmark:** Delivered a **3.2x performance boost** on code parsing times (reducing average parsing from `0.122s` to `0.038s` per 30 files) with zero regression in symbol correctness.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 14** (App Router) | Modern, fast React framework for static/server-side rendering. |
| | **TypeScript** | Strict static type-safety across components. |
| | **Tailwind CSS** | Premium aesthetics, utility-first layout styling. |
| | **Framer Motion** | Micro-animations and fluid, interactive state transitions. |
| | **Mermaid.js** | Dynamic client-side rendering of system diagrams. |
| **Backend** | **FastAPI** | High-performance Python ASGI web framework. |
| | **SQLAlchemy & Alembic** | ORM mapper and schema migration manager. |
| | **Tree-sitter** | Ultra-fast AST symbol scanner and parser. |
| **Vector DB**| **ChromaDB** | Semantic embedding storage and dense vector retrieval. |
| **Database** | **PostgreSQL** | Relational metadata store (Neon Serverless). |
| **AI/LLM**   | **OpenRouter API** | Interface to leading LLMs (Gemini, GPT) & vector embeddings. |

---

## 🚀 Getting Started

### Prerequisites
Make sure you have the following installed on your machine:
*   [Node.js](https://nodejs.org/) (v18.0.0 or higher)
*   [Python](https://www.python.org/) (v3.10.0 or higher)
*   [Git](https://git-scm.com/)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/repolens-ai.git
cd repolens-ai
```

---

### Step 2: Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    ```

3.  **Activate the virtual environment:**
    *   **Windows (PowerShell):**
        ```powershell
        .venv\Scripts\Activate.ps1
        ```
    *   **macOS / Linux:**
        ```bash
        source .venv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure environment variables:**
    Create a `.env` file in the `backend` folder and populate it with your keys:
    ```env
    # Database URL (Defaults to local SQLite if omitted)
    DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
    
    # Chroma Vector Database Folder
    CHROMA_PERSIST_DIR=./chroma_db
    
    # OpenRouter LLM Setup
    OPENAI_API_KEY=your-openrouter-api-key
    OPENAI_BASE_URL=https://openrouter.ai/api/v1
    
    # Selected Models
    EMBEDDING_MODEL=openai/text-embedding-3-small
    CHAT_MODEL=openrouter/free # Or your choice of model
    
    # File storage paths
    CLONE_DIR=./repos
    
    # Chunk settings
    MAX_CHUNK_SIZE=1500
    CHUNK_OVERLAP=200
    ```

6.  **Run migrations / database setup:**
    ```bash
    alembic upgrade head
    ```

7.  **Start the FastAPI development server:**
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
    *The API will be available at `http://localhost:8000`. You can inspect the Swagger docs at `http://localhost:8000/docs`.*

---

### Step 3: Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd ../frontend
    ```

2.  **Install npm packages:**
    ```bash
    npm install
    ```

3.  **Start the Next.js development server:**
    ```bash
    npm run dev
    ```
    *The frontend dashboard will be available at `http://localhost:3000`.*

---

## 🔌 API Reference

### Repositories `/repos`

*   `POST /repos/import` - Clones a public GitHub URL and initializes background ingestion.
*   `GET /repos` - Lists all imported repositories and their current status (`cloning`, `parsing`, `indexing`, `ready`, `failed`).
*   `GET /repos/{repo_id}` - Fetches metadata and parsing progress for a specific repository.
*   `DELETE /repos/{repo_id}` - Deletes repository metadata, cloned filesystem folder, and ChromaDB vector index.

### Analysis `/repos`

*   `POST /repos/{repo_id}/analyze` - Manually triggers indexing and parsing for a repository.
*   `GET /repos/{repo_id}/summary` - Returns a comprehensive generated overview of the codebase.
*   `GET /repos/{repo_id}/architecture` - Returns generated system component analysis and dynamic Mermaid graph payloads.
*   `GET /repos/{repo_id}/onboarding` - Generates a targeted developer onboarding markdown guide.

### Chat `/repos`

*   `POST /repos/{repo_id}/chat` - Submit a natural-language query. Returns a grounded answer with relevant file citations.
*   `GET /repos/{repo_id}/chat/history` - Retrieves recent chat history log for the repository.

---

<p align="center">Made with ❤️ by Manan Shah</p>
