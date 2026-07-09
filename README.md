# ● Crate — AI Support Agent

> A production-grade **ReAct agent** for e-commerce customer support, built with **LangGraph**, **FastAPI**, **Streamlit**, **SQLite**, and **Langfuse** observability.

---

## 🏗️ Architecture

![Architecture](images/architecture.png)

| Layer | Technology | Role |
|---|---|---|
| **Chat UI** | Streamlit | Customer-facing interface with quick actions |
| **Gateway** | FastAPI | `POST /api/v1/chat` — async, typed, CORS |
| **Agent** | LangGraph | ReAct loop: Triage → Tool → Response (with retry) |
| **Tools** | 7 function-calling tools | Order lookup, shipping tracking, returns |
| **Storage** | SQLite | 12 orders + 9 shipments (auto-seeded) |
| **Observability** | Langfuse | LLM calls, latency, cost, tool execution |

### ReAct Flow

```
User Message → Triage (classify) → Tool (execute) → Response (compose)
                    ↑                                    │
                    └────────── retry (max 3) ←──────────┘
```

| Step | Node | Description |
|---|---|---|
| 1 | `triage_node` | GPT-4o-mini classifies intent & extracts entities |
| 2 | `tool_node` | LLM selects the right tool → executes against SQLite |
| 3 | `after_tools` | Error check — retry up to 3 times on failure |
| 4 | `response_node` | LLM composes a natural English reply |
| 5 | Fallback | If Turkish leaks → raw English tool results used |

---

## ✨ Features

- **7 Tools** — `lookup_order`, `lookup_orders_by_email`, `search_orders`, `track_shipment`, `get_return_policy`, `check_return_eligibility`, `initiate_return`
- **Retry Loop** — Up to 3 retries on tool errors
- **English-Only** — Prompts + Turkish detection fallback
- **SQLite** — 12 orders, 9 shipments (auto-created on startup)
- **Langfuse** — Every LLM call, tool execution, latency & cost tracked
- **24 Tests** — Services, tools, graph (no LLM required)
- **Single Command** — `python run.py` starts everything

---

## 🚀 Quick Start

```bash
# 1. Setup
python -m venv venv
venv\Scripts\activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
copy .env.example .env         # Add your OPENAI_API_KEY

# 3. Run
python run.py                  # → http://localhost:8501
```

> **Optional:** Add `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` to `.env` for tracing.

```bash
# 4. Test
pytest tests/ -v               # 24 tests
```

---

## 📡 API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/chat` | Send message → agent response |

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Where is my package FDX-78901234?"}'
```

---

## 🎯 Sample Queries

| Query | Flow |
|---|---|
| `What's the status of order ORD-1002?` | Triage → `lookup_order` → Response |
| `Where is package FDX-78901234?` | Triage → `track_shipment` → Response |
| `What is your return policy?` | Triage → `get_return_policy` → Response |
| `I want to return ORD-1001` | Triage → `check_return_eligibility` → Response |
| `Show orders for james@example.com` | Triage → `lookup_orders_by_email` → Response |
| `Find my keyboard order` | Triage → `search_orders("keyboard")` → Response |

---

## 📁 Project Structure

```
e-commerce/
├── run.py                      # Single-command launcher
├── images/
│   └── architecture.png        # Architecture diagram
├── src/
│   ├── agent/                  # LangGraph: state, tools, nodes, graph
│   ├── services/               # SQLite: orders, shipping, returns
│   ├── observability/          # Langfuse integration
│   ├── api/                    # FastAPI: schemas, routes
│   └── ui/                     # Streamlit chat interface
├── data/                       # SQLite DB (auto-created)
└── tests/                      # 24 unit tests
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent | LangGraph (StateGraph) |
| LLM | OpenAI GPT-4o-mini (function calling) |
| API | FastAPI + Pydantic v2 |
| UI | Streamlit |
| Database | SQLite |
| Observability | Langfuse |
| Testing | pytest |

---

## 📝 License

MIT — Built for learning & portfolio purposes.
