# LLM Consulate

**One Prompt. Multiple Minds.**

A production-quality multi-model AI platform. Consult multiple open-source language models through a single interface — where AI models confer before they answer.

## Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│  Next.js Frontend   │  SSE    │  FastAPI Backend     │
│  (Vercel)           │ ──────► │  (Railway / Render)  │
│                     │         │                      │
│  • Chat UI          │         │  • Orchestrators     │
│  • Landing / SEO    │         │  • NVIDIA Provider   │
│  • Local state      │         │  • Model Registry    │
└─────────────────────┘         └──────────┬───────────┘
                                           │
                                           ▼
                                ┌──────────────────────┐
                                │  NVIDIA Inference API │
                                │  integrate.api.nvidia │
                                └──────────────────────┘
```

## Features

- **Direct Chat** — Stream responses from any open-source model
- **Consulate Mode** — Parallel multi-model reasoning with consensus synthesis
- **Pure Python orchestration** — No LangChain, no AI frameworks
- **SSE streaming** — Real-time tokens for both modes
- **Guest experience** — 15 requests per session, local conversation history
- **SEO-optimized landing** — Sitemap, robots, JSON-LD, indexable content

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env and set NVIDIA_API_KEY

uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
# From project root
npm install
cp .env.example .env.local
# Edit .env.local — set NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

Open [http://localhost:3000](http://localhost:3000) for the landing page, [http://localhost:3000/chat](http://localhost:3000/chat) to chat.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `NVIDIA_API_KEY` | NVIDIA Inference API key |
| `NVIDIA_BASE_URL` | Default: `https://integrate.api.nvidia.com/v1` |
| `SYNTHESIS_MODEL_ID` | Registry ID for consensus synthesis |
| `SESSION_REQUEST_LIMIT` | Guest request limit (default: 15) |
| `CORS_ORIGINS` | Comma-separated allowed origins |

### Frontend (`.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | FastAPI backend URL |
| `NEXT_PUBLIC_APP_URL` | Public app URL for SEO |

## The Council

Six open-source models, each with a distinct role:

| Model | Role | NVIDIA ID |
|-------|------|-----------|
| GPT-OSS 120B | Chief Analyst | `openai/gpt-oss-120b` |
| MiniMax M2.7 | Strategic Advisor | `minimaxai/minimax-m2.7` |
| Qwen3 Next 80B | Research Specialist | `qwen/qwen3-next-80b-a3b-instruct` |
| Nemotron Omni 30B | Independent Reviewer | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` |
| Kimi K2.6 | Creative Expert | `moonshotai/kimi-k2.6` |
| Gemma 3N E2B | Conservative Analyst | `google/gemma-3n-e2b-it` |

### Constitutional Crisis Mode

When council agreement falls below 60%, the system returns `status: deadlock` instead of fabricating consensus. The frontend displays **Council Deadlocked** with majority and minority positions.

### Minority Report

When individual models strongly diverge from the majority, their dissenting views are surfaced as expandable **Minority Report** panels.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check + provider status |
| `GET` | `/api/models` | Available council members |
| `POST` | `/api/chat` | Single-model streaming chat |
| `POST` | `/api/consulate` | Full council session with consensus/deadlock |

All streaming endpoints return Server-Sent Events.

## Adding a Model

Edit `backend/app/models/registry.py`:

```python
"my-model": ModelConfig(
    id="my-model",
    display_name="My Model",
    provider_model_id="vendor/model-name",
    description="...",
    context_limit=8192,
    capabilities=("chat",),
    consulate_eligible=True,
    family="MyFamily",
),
```

The frontend model picker updates automatically.

## Deployment

### Frontend → Vercel

```bash
vercel deploy
```

Set `NEXT_PUBLIC_API_URL` to your backend URL.

### Backend → Railway / Render

```bash
cd backend
# Railway: connect repo, set root to /backend
# Render: use Dockerfile
```

Set `CORS_ORIGINS` to your Vercel domain.

## Tech Stack

**Frontend:** Next.js 15, TypeScript, Tailwind CSS 4, shadcn/ui, Framer Motion, Zustand

**Backend:** FastAPI, Python 3.12+, httpx, Pydantic, asyncio

## License

MIT
