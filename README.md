# LLM Consulate
 
**One Prompt. Multiple Minds.**
 
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Deployed on Vercel](https://img.shields.io/badge/Deployed-Vercel-black?logo=vercel&logoColor=white)](https://llm-consulate.vercel.app/)
[![NVIDIA Inference](https://img.shields.io/badge/Inference-NVIDIA-76b900?logo=nvidia&logoColor=white)](https://www.nvidia.com/en-us/ai/)
 
> Consult a council instead of a single machine.
 
[**Live Demo**](https://llm-consulate.vercel.app/) · [**Chat Interface**](https://llm-consulate.vercel.app/chat) · [**How It Works**](https://llm-consulate.vercel.app/#how-it-works)
 
---
 
## Executive Summary
 
LLM Consulate is a production-quality multi-model AI platform that sends a single prompt to a council of open-source language models, collects independent reasoning, measures inter-model agreement, and synthesizes a unified response — without concealing disagreement.
 
Where conventional AI products return one answer from one model, LLM Consulate treats model divergence as signal, not noise. When the council reaches sufficient agreement, it synthesizes. When it cannot, it says so.
 
Built on a pure-Python FastAPI backend with async SSE streaming and a Next.js 15 frontend, the system requires no AI orchestration frameworks and introduces no hidden abstractions between the orchestrator and the inference provider.
 
No sign-up. No API keys for guests. 15 free requests per session.
 
---
 
## Project Vision
 
Most AI products hide their reasoning. A single model responds, and you receive a single answer with no visibility into confidence, coverage gaps, or alternative interpretations.
 
LLM Consulate is built on a different premise: important questions deserve more than one point of view. Independent models cross-check each other. Agreement builds confidence. Disagreement surfaces nuance. The final synthesis is always traceable back to the individual responses that produced it.
 
The platform is designed for thoughtful inquiry — not rapid Q&A. The deliberate, council-based UX reflects that intent.
 
---
 
## Why LLM Consulate Exists
 
Single-model AI has three structural failure modes:
 
**Confident wrongness.** A model can produce a well-formed, fluent, incorrect answer with no signal to the user that it is wrong. Cross-model disagreement is the most accessible check on this behavior.
 
**Domain gaps.** Every model has training gaps. No single model covers all domains equally. Different architectures and training corpora produce different strengths. A council of models with varied provenance covers more ground than any individual participant.
 
**Hidden bias.** A model trained on a particular corpus will reflect the biases of that corpus. Independent models originating from different institutions and training runs provide partial correction for this.
 
LLM Consulate operationalizes these observations into a concrete product: parallel reasoning, measured consensus, surfaced dissent.
 
---
 
## Core Concept
 
```
User Prompt
     │
     ├── Model A ──► Response A ──┐
     ├── Model B ──► Response B ──┤
     ├── Model C ──► Response C ──┼──► Agreement Score ──► Synthesis
     ├── Model D ──► Response D ──┤                           │
     └── Model E ──► Response E ──┘                     Final Answer
                                                    (or: Deadlock Report)
```
 
Every model in the council receives the same prompt. Every model responds independently. A synthesis engine evaluates agreement, resolves divergence where possible, and produces a final response that reflects the strongest reasoning across all participants.
 
If inter-model agreement falls below 60%, the system does not fabricate consensus. It surfaces a **Constitutional Crisis**: majority and minority positions are presented separately, and the user is shown the disagreement directly.
 
---
 
## Product Walkthrough
 
**Direct Chat** gives users a standard streaming chat interface against any single model in the registry. It behaves like a conventional model chat — except every model available is open-source, served through NVIDIA's inference platform.
 
**Consulate Mode** is the core product experience:
 
1. The user submits a prompt.
2. The same prompt is dispatched concurrently to each council member.
3. Responses stream back in real time. Progress indicators show which models have responded.
4. Once all responses are collected, the synthesis engine generates a final, unified answer.
5. The user can expand any individual model response to inspect the raw reasoning that informed the synthesis.
6. If a model strongly disagrees with the majority position, its dissent is surfaced as a **Minority Report** — expandable, attributed, and never flattened into the consensus.
**Local History** persists conversations in the browser. Users can create, rename, and manage multiple conversation threads with no account.
 
---
 
## Feature Matrix
 
| Feature | Direct Chat | Consulate Mode |
|---|---|---|
| Single model response | ✓ | — |
| Parallel multi-model dispatch | — | ✓ |
| Real-time SSE streaming | ✓ | ✓ |
| Consensus synthesis | — | ✓ |
| Inter-model agreement score | — | ✓ |
| Minority Report (dissent surfacing) | — | ✓ |
| Constitutional Crisis detection | — | ✓ |
| Individual response inspection | ✓ | ✓ |
| Browser-local conversation history | ✓ | ✓ |
| No sign-up required | ✓ | ✓ |
| Open-source models only | ✓ | ✓ |
 
---
 
## Key Features
 
**Pure Python Orchestration.** All multi-model coordination is implemented directly in Python using `asyncio` and `httpx`. No LangChain, no AI orchestration framework, no hidden abstraction layer. Every orchestration decision is visible in the source.
 
**SSE Streaming.** Both the direct chat and consulate endpoints stream tokens using Server-Sent Events. The frontend receives incremental updates as each model responds, rather than waiting for all models to complete before rendering.
 
**Registry Pattern.** Models are declared as structured configuration objects in a centralized registry. Adding a new model requires no changes to orchestration logic, synthesis logic, or frontend code. The registry drives the UI automatically.
 
**Constitutional Crisis Mode.** When inter-model agreement falls below 60%, the system enters a deadlock state. The frontend renders `Council Deadlocked` and presents majority and minority positions separately. The system never synthesizes a false consensus.
 
**Minority Reports.** When individual council members diverge significantly from the majority position, their dissenting reasoning is preserved and surfaced as expandable Minority Reports. Dissent is first-class content, not filtered noise.
 
**Transparent Reasoning.** Every Consulate Mode response is fully decomposable. Users can inspect each model's individual answer, the agreement score, any minority positions, and the synthesis reasoning.
 
**Guest Experience.** 15 requests per session with conversation history stored locally in the browser. No account, no API key, no friction.
 
---
 
## Constitutional Crisis Mode
 
When the council reaches deadlock, the system enters **Constitutional Crisis Mode**.
 
```
Agreement Score < 60%
 
status: DEADLOCK
 
┌─────────────────────────────────────────┐
│          Council Deadlocked             │
│                                         │
│  Majority Position (N models)           │
│  ─────────────────────────────────────  │
│  [majority reasoning]                   │
│                                         │
│  Minority Position (N models)           │
│  ─────────────────────────────────────  │
│  [minority reasoning]                   │
└─────────────────────────────────────────┘
```
 
The system does not fabricate consensus when models cannot agree. This is an intentional design decision: a synthesized answer built from deep disagreement is less trustworthy than an honest presentation of the disagreement itself. Constitutional Crisis Mode communicates this directly to the user.
 
---
 
## Minority Reports
 
When an individual model takes a position that diverges substantially from the majority, its reasoning is preserved as a **Minority Report** — an expandable section within the Consulate response.
 
Minority Reports are attributed to the specific model that produced them. They are never folded into the synthesis and never suppressed. In some cases, the minority position may be the more accurate one.
 
---
 
## Architecture Overview
 
```
┌─────────────────────┐         ┌──────────────────────┐
│  Next.js Frontend   │   SSE   │   FastAPI Backend    │
│  (Vercel)           │ ──────► │  (Railway / Render)  │
│                     │         │                      │
│  • Chat UI          │         │  • Orchestrators     │
│  • Landing / SEO    │         │  • NVIDIA Provider   │
│  • Local state      │         │  • Model Registry    │
│  • Zustand          │         │  • Pydantic models   │
└─────────────────────┘         └──────────┬───────────┘
                                           │
                                           ▼
                               ┌──────────────────────┐
                               │  NVIDIA Inference    │
                               │  integrate.api.nvidia│
                               └──────────────────────┘
```
 
**Frontend (Vercel):** A Next.js 15 application with TypeScript, Tailwind CSS 4, shadcn/ui, Framer Motion, and Zustand. The frontend owns the chat UI, landing page, SEO metadata (sitemap, robots.txt, JSON-LD), and all local state. Conversation history is stored in the browser; the frontend is stateless with respect to the backend.
 
**Backend (Railway / Render):** A FastAPI application in Python 3.12+. It exposes the orchestration logic, the model registry, and the inference provider integration. All multi-model coordination runs here as async Python. The backend communicates with the NVIDIA Inference API for all model calls.
 
**NVIDIA Inference API:** The inference provider. Every open-source model in the registry is served through NVIDIA's `integrate.api.nvidia.com` endpoint. The backend abstracts the provider, meaning the inference layer could be swapped independently of orchestration logic.
 
---
 
## Request Lifecycle
 
**Direct Chat**
 
```
Client ──POST /api/chat──► FastAPI
                              │
                     Resolve model from registry
                              │
                     Stream tokens via NVIDIA API
                              │
                     SSE ──────────────────────► Client
```
 
**Consulate Mode**
 
```
Client ──POST /api/consulate──► FastAPI Orchestrator
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
              Model A call         Model B call         Model C call
              (async)              (async)              (async)
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         │
                             Collect all responses
                                         │
                             Compute agreement score
                                         │
                          ┌──────────────┴──────────────┐
                    score ≥ 60%                    score < 60%
                          │                              │
                   Synthesis engine             Constitutional Crisis
                          │                              │
                  Unified response             Majority + Minority
                          │                              │
                    SSE ──┴──────────────────────────────┴──► Client
```
 
All model calls in Consulate Mode are dispatched concurrently. The orchestrator waits for all responses before computing agreement and triggering synthesis.
 
---
 
## Council Composition
 
The default council comprises six open-source models, each with a defined role in the deliberation:
 
| Model | Role | Provider Model ID |
|---|---|---|
| GPT-OSS 120B | Chief Analyst | `openai/gpt-oss-120b` |
| MiniMax M2.7 | Strategic Advisor | `minimaxai/minimax-m2.7` |
| Qwen3 Next 80B | Research Specialist | `qwen/qwen3-next-80b-a3b-instruct` |
| Nemotron Omni 30B | Independent Reviewer | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` |
| Kimi K2.6 | Creative Expert | `moonshotai/kimi-k2.6` |
| Gemma 3N E2B | Conservative Analyst | `google/gemma-3n-e2b-it` |
 
The council is designed with intentional diversity: models from different institutions, with different training corpora, parameter scales, and architectural families. This maximizes the value of cross-model comparison and reduces the likelihood that all models share the same blind spots.
 
All models are open-source. All are served through NVIDIA's inference platform. None require proprietary API access from the user.
 
---
 
## Technology Choices
 
### Frontend
 
| Technology | Version | Role |
|---|---|---|
| Next.js | 15 | React framework, routing, SSE client, SEO |
| TypeScript | — | Type safety across the frontend codebase |
| Tailwind CSS | 4 | Utility-first styling |
| shadcn/ui | — | Accessible component primitives |
| Framer Motion | — | Animation and transition layer |
| Zustand | — | Lightweight client-side state management |
 
### Backend
 
| Technology | Version | Role |
|---|---|---|
| FastAPI | — | Async HTTP server and SSE streaming |
| Python | 3.12+ | Runtime |
| httpx | — | Async HTTP client for NVIDIA API calls |
| Pydantic | — | Request/response validation and model config |
| asyncio | — | Concurrent model dispatch in Consulate Mode |
 
---
 
## Why No LangChain
 
LLM Consulate's orchestration is implemented in pure Python. This is an explicit architectural decision, not an oversight.
 
**What LangChain adds:** Abstraction layers for prompt templates, chains, agents, memory, and tool calling. Useful for rapid prototyping across many providers.
 
**What LangChain costs:** Non-trivial complexity for debugging multi-step chains, framework-specific abstractions that obscure what is actually happening at the HTTP level, dependency weight, and tight coupling to framework design decisions.
 
**Why it was avoided here:** The orchestration logic in LLM Consulate — parallel model dispatch, agreement scoring, synthesis, deadlock detection — maps directly to async Python primitives. `asyncio.gather` for concurrent dispatch. `httpx.AsyncClient` for streaming calls. Pydantic for validation. There is no conceptual gap between the problem and the implementation that a framework would close.
 
The result is a codebase where every orchestration decision is visible, testable, and modifiable without understanding a framework's internal model. For contributors, this means no prerequisite framework knowledge.
 
---
 
## Engineering Tradeoffs
 
### SSE vs WebSockets
 
LLM Consulate uses Server-Sent Events (SSE) rather than WebSockets for streaming.
 
**SSE:** Unidirectional (server to client), HTTP-native, trivially proxied by Vercel and Cloudflare, automatic reconnect built into the browser EventSource API, stateless on the server.
 
**WebSockets:** Bidirectional, requires persistent connection management, more complex to proxy and deploy, introduces server-side session state.
 
For token streaming — where the client sends one request and receives a stream of tokens — SSE is the correct primitive. The bidirectionality of WebSockets is unnecessary overhead. SSE aligns with the request/response model of HTTP and simplifies both the backend and the deployment topology.
 
### Registry Pattern
 
Models are declared in `backend/app/models/registry.py` as `ModelConfig` objects. The registry is the single source of truth for model metadata: display name, provider model ID, context limits, capabilities, and consulate eligibility.
 
**Benefits:** New models can be added without modifying orchestration logic. The frontend consumes the registry dynamically via `GET /api/models`. Consulate eligibility is expressed declaratively per model, not encoded in call sites.
 
**Tradeoff:** Registry-driven systems can become complex to reason about when model-specific behavior needs to diverge significantly. For the current surface area, the pattern is appropriate.
 
### Consensus Synthesis
 
The synthesis engine receives all model responses and produces a unified answer. Agreement is scored before synthesis is attempted.
 
**Why this matters:** Naive synthesis — averaging or interpolating responses — can produce an answer that no individual model would endorse and that obscures real disagreement. The 60% threshold and Constitutional Crisis Mode exist to prevent this. The system only synthesizes when there is a defensible majority position to synthesize from.
 
---
 
## Repository Structure
 
```
llm-consulate/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── registry.py          # Model registry — single source of truth
│   │   ├── orchestrators/           # Consulate and direct chat orchestration
│   │   └── providers/               # NVIDIA inference provider abstraction
│   ├── main.py                      # FastAPI app entrypoint
│   ├── requirements.txt
│   └── .env.example
├── frontend/                        # Next.js 15 application
│   ├── app/
│   │   ├── chat/                    # Chat interface route
│   │   └── page.tsx                 # Landing page
│   ├── components/                  # UI components (shadcn/ui, custom)
│   ├── lib/                         # Zustand stores, API client, utilities
│   ├── public/                      # Sitemap, robots.txt, static assets
│   ├── package.json
│   └── .env.example
└── README.md
```
 
---
 
## Local Development
 
### Prerequisites
 
- Python 3.12+
- Node.js 18+
- An NVIDIA Inference API key ([get one here](https://www.nvidia.com/en-us/ai/))
### Backend
 
```bash
cd backend
 
# Create and activate a virtual environment
python -m venv venv
 
# macOS / Linux
source venv/bin/activate
 
# Windows
venv\Scripts\activate
 
# Install dependencies
pip install -r requirements.txt
 
# Configure environment
cp .env.example .env
# Set NVIDIA_API_KEY in .env
 
# Start the development server
uvicorn main:app --reload --port 8000
```
 
The backend will be available at `http://localhost:8000`.
 
### Frontend
 
```bash
# From the repository root or frontend/ directory
npm install
 
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
 
npm run dev
```
 
| URL | Description |
|---|---|
| `http://localhost:3000` | Landing page |
| `http://localhost:3000/chat` | Chat interface |
| `http://localhost:8000/api/health` | Backend health check |
| `http://localhost:8000/docs` | FastAPI auto-generated API docs |
 
---
 
## Environment Variables
 
### Backend (`backend/.env`)
 
| Variable | Required | Description |
|---|---|---|
| `NVIDIA_API_KEY` | **Yes** | API key for NVIDIA Inference (`integrate.api.nvidia.com`) |
| `NVIDIA_BASE_URL` | No | Override for the NVIDIA inference base URL |
| `SYNTHESIS_MODEL_ID` | No | Model used for the synthesis step in Consulate Mode |
| `SESSION_REQUEST_LIMIT` | No | Max requests per guest session (default: 15) |
| `CORS_ORIGINS` | **Yes (prod)** | Comma-separated list of allowed frontend origins |
 
### Frontend (`frontend/.env.local`)
 
| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | **Yes** | Full URL of the FastAPI backend (e.g. `http://localhost:8000`) |
| `NEXT_PUBLIC_APP_URL` | No | Canonical URL of the frontend app (used for SEO metadata) |
 
---
 
## API Reference
 
All streaming endpoints use Server-Sent Events. Non-streaming endpoints return JSON.
 
### `GET /api/health`
 
Returns the health status of the backend.
 
**Response**
 
```json
{ "status": "ok" }
```
 
---
 
### `GET /api/models`
 
Returns the full model registry. Used by the frontend to populate model selection UI.
 
**Response**
 
```json
[
  {
    "id": "gpt-oss-120b",
    "display_name": "GPT-OSS 120B",
    "description": "...",
    "context_limit": 8192,
    "capabilities": ["chat"],
    "consulate_eligible": true,
    "family": "GPT-OSS"
  }
]
```
 
---
 
### `POST /api/chat`
 
Stream a response from a single model.
 
**Request body**
 
```json
{
  "model_id": "gpt-oss-120b",
  "messages": [
    { "role": "user", "content": "Explain quantum entanglement." }
  ]
}
```
 
**Response:** SSE stream. Each event contains an incremental token or a terminal `[DONE]` event.
 
---
 
### `POST /api/consulate`
 
Dispatch a prompt to the full council and receive streamed consensus output.
 
**Request body**
 
```json
{
  "messages": [
    { "role": "user", "content": "What are the long-term consequences of AGI?" }
  ],
  "model_ids": ["gpt-oss-120b", "qwen3-next-80b", "kimi-k2.6"]
}
```
 
**Response:** SSE stream. Events include per-model response chunks, an agreement score event, and a synthesis stream (or a deadlock event if agreement < 60%).
 
---
 
## Deployment Guide
 
### Frontend — Vercel
 
The frontend is designed for Vercel. No special configuration is required beyond standard Next.js deployment.
 
1. Connect the repository to Vercel.
2. Set `NEXT_PUBLIC_API_URL` to your deployed backend URL in the Vercel environment variables dashboard.
3. Set `NEXT_PUBLIC_APP_URL` to your Vercel deployment URL for canonical SEO metadata.
4. Deploy.
Vercel handles SSE streaming natively via its edge network.
 
### Backend — Railway or Render
 
The backend is a standard FastAPI/uvicorn application. It can be deployed to Railway, Render, Fly.io, or any platform that supports Python web services.
 
**Environment variables to configure in production:**
 
```
NVIDIA_API_KEY=<your-key>
CORS_ORIGINS=https://your-frontend-domain.vercel.app
SESSION_REQUEST_LIMIT=15
```
 
**Start command:**
 
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
 
Ensure `CORS_ORIGINS` is set to your exact frontend domain. Wildcard origins are not recommended in production.
 
---
 
## Adding New Models
 
All models are registered in `backend/app/models/registry.py`. Adding a model requires a single dictionary entry. No changes to orchestration logic, synthesis logic, or frontend code are necessary.
 
```python
"my-model-id": ModelConfig(
    id="my-model-id",
    display_name="My Model Name",
    provider_model_id="vendor/model-name-on-nvidia",
    description="One-sentence description of the model's strengths.",
    context_limit=8192,
    capabilities=("chat",),
    consulate_eligible=True,   # Include in Consulate Mode council
    family="ModelFamily",
)
```
 
**`consulate_eligible`** controls whether the model participates in Consulate Mode. Set to `False` for models you want available in Direct Chat only — for example, smaller models that may not contribute meaningfully to multi-model synthesis.
 
After adding a new entry, `GET /api/models` will return it and the frontend will render it automatically.
 
**Validation checklist for new models:**
 
- Verify `provider_model_id` matches the model string on `integrate.api.nvidia.com`
- Confirm the model supports chat completion (not instruction-tuned for a different task)
- Test streaming behavior against `POST /api/chat` before enabling `consulate_eligible`
- Update `context_limit` to match the model's actual context window
---
 
## Contributor Guide
 
### How Orchestration Works
 
The Consulate orchestrator receives a list of model IDs and a messages array. It dispatches concurrent async HTTP calls to the NVIDIA provider for each model, collects responses, scores agreement, and routes to synthesis or deadlock handling.
 
```
ConsulateOrchestrator.run(model_ids, messages)
    │
    ├── asyncio.gather(*[provider.call(model, messages) for model in model_ids])
    │
    ├── agreement_score = compute_agreement(responses)
    │
    ├── if score >= 0.60 → SynthesisEngine.synthesize(responses)
    └── if score <  0.60 → DeadlockHandler.report(responses)
```
 
### How Council Members Work
 
Each council member is a `ModelConfig` entry in the registry. The orchestrator treats them identically — the roles (Chief Analyst, Strategic Advisor, etc.) are display metadata for the UI, not behavioral configuration. The models are not prompted with their roles; the roles communicate to the user what each model's architectural strengths are understood to be.
 
### How Synthesis Works
 
The synthesis engine receives all model responses and constructs a prompt that asks a synthesis model (configured via `SYNTHESIS_MODEL_ID`) to produce a unified answer reflecting the majority position. Minority positions identified during agreement scoring are preserved separately and not passed to the synthesis prompt as ground truth.
 
### How Model Registration Works
 
The registry is a Python dictionary keyed by model ID string, with `ModelConfig` values. The registry is imported by the orchestrator (to resolve model calls), the provider (to look up `provider_model_id`), and the `/api/models` endpoint (to serialize the registry for the frontend).
 
### How Streaming Works
 
Each provider call opens an async streaming connection to the NVIDIA API and yields tokens as they arrive. The FastAPI endpoints use `StreamingResponse` with an async generator that yields SSE-formatted events. The Next.js frontend uses the browser's `EventSource` API (or a polyfill for POST-based SSE) to consume the stream and update component state incrementally.
 
---
 
## Design Principles
 
**Honesty over confidence.** The system reports deadlock when it cannot synthesize. It never constructs a false consensus. This is a product decision as much as an engineering one.
 
**Transparency as a feature.** Individual model responses are always accessible. Minority reports are surfaced, not suppressed. The user can always understand how the final answer was produced.
 
**No hidden framework behavior.** Pure Python orchestration means every step in the reasoning pipeline is explicit in the source. There are no surprise behaviors introduced by a framework's internal chain logic.
 
**Open source by default.** Every model in the registry is open source. This is a scope constraint and a values statement: the platform is built around models whose weights are publicly available, not proprietary systems.
 
**Registry-driven extensibility.** New models, new capabilities, and new council configurations are expressed as data, not code. The system is designed to grow without requiring changes to its core logic.
 
---
 
## Production Considerations
 
**Streaming architecture.** Both endpoints use SSE. In production, ensure your hosting platform supports long-lived HTTP connections and does not impose aggressive connection timeouts. Vercel's edge network handles this correctly for the frontend's fetch calls; backend hosting platforms vary.
 
**Failure handling.** If an individual model call fails during Consulate Mode (network error, provider timeout, rate limit), the orchestrator must handle partial council responses gracefully. Deployments should monitor for degraded councils and surface partial results rather than failing the entire request.
 
**Consensus degradation.** As models are added or removed from the registry, the agreement scoring behavior will shift. The 60% threshold is configured as a parameter — it should be revisited if the council composition changes significantly.
 
**Session limits.** The guest experience is capped at 15 requests per session, enforced via `SESSION_REQUEST_LIMIT`. This is a server-side parameter, not a client-side soft cap. Adjust based on your inference cost envelope.
 
**Provider abstraction.** The NVIDIA provider is the sole inference backend. The `NVIDIA_BASE_URL` environment variable allows the base URL to be overridden without code changes, providing a path to swap inference providers at the configuration level.
 
**CORS configuration.** In production, `CORS_ORIGINS` must be set to the exact frontend domain. An unconfigured or wildcard CORS policy in production is a security risk.
 
---
 
## Performance Considerations
 
**Concurrent model dispatch.** Consulate Mode dispatches all model calls concurrently using `asyncio.gather`. The wall-clock latency of a Consulate response is bounded by the slowest responding model, not by the sum of all response times. For a six-model council, this is a significant improvement over sequential dispatch.
 
**Streaming token delivery.** SSE streaming delivers tokens to the frontend as they arrive from each model. Users see progressive output rather than waiting for all models to complete. This is particularly important for Consulate Mode, where the total response volume is much higher than a single-model response.
 
**Context limits.** Each model's `context_limit` is declared in the registry. Orchestration logic should respect these limits when constructing prompts, particularly for synthesis steps that concatenate multiple model responses.
 
---
 
## Security Considerations
 
**API key management.** `NVIDIA_API_KEY` must never be exposed to the frontend. The backend is the sole holder of the API key and the sole caller of the NVIDIA inference endpoint. `NEXT_PUBLIC_*` variables are bundled into the frontend JavaScript; never set an API key as a `NEXT_PUBLIC_*` variable.
 
**CORS policy.** Configure `CORS_ORIGINS` explicitly in production. The backend should reject requests from origins not in the allowlist.
 
**Session request limits.** The 15-request guest limit is the primary abuse prevention mechanism for unauthenticated users. The `SESSION_REQUEST_LIMIT` variable should be set conservatively in production and adjusted based on observed usage.
 
**Input validation.** FastAPI and Pydantic validate all incoming request bodies against defined schemas. Ensure model IDs in `POST /api/consulate` are validated against the registry — reject requests referencing model IDs not present in the registry.
 
---
 
## Future Roadmap
 
Based on the current architecture, natural extensions include:
 
- **Weighted council voting** — models with stronger track records on a domain class receive higher weight in agreement scoring
- **Council configuration UI** — allow users to select which models participate in a given Consulate session
- **Persistent history** — optional account-backed conversation storage beyond the browser-local session
- **Custom synthesis prompts** — allow users to configure how the synthesis engine is prompted
- **Model performance telemetry** — latency and agreement rate tracking per model over time
- **Additional inference providers** — the provider abstraction layer supports routing to non-NVIDIA endpoints at the configuration level
---
 
## Screenshots
 
*Screenshots of the live interface are available at [llm-consulate.vercel.app](https://llm-consulate.vercel.app/).*
 
| View | Description |
|---|---|
| Landing page | Product positioning, How It Works walkthrough, FAQ |
| Direct Chat | Single-model streaming chat interface |
| Consulate Mode | Parallel response view with progress indicators and synthesis output |
| Minority Report | Expandable dissenting model response within a Consulate answer |
| Constitutional Crisis | Deadlock display with majority and minority position presentation |
 
---
 
## Contributing
 
Contributions are welcome. The most impactful areas for contribution:
 
- **New council members** — models available on NVIDIA Inference that are not yet in the registry
- **Orchestration improvements** — agreement scoring algorithms, synthesis prompt engineering
- **Frontend UX** — response visualization, streaming state management, accessibility
- **Documentation** — architecture explanations, runbooks, contributor guides
**To contribute:**
 
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit using [Conventional Commits](https://www.conventionalcommits.org/): `git commit -m 'feat: describe your change'`
4. Push: `git push origin feature/your-feature-name`
5. Open a Pull Request targeting `main`
For significant architectural changes, open an issue first to discuss the approach before implementing.
 
---
 
## License
 
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
 
---
 
*Open-source models only. Built with intention.*
 
