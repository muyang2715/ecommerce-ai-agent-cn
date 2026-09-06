"""
FastAPI Application — Agent Gateway entry point.

Run with:
    uvicorn src.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config import settings
from src.services.database import init_db
from src.observability.langfuse_setup import get_langfuse_client, init_langfuse

app = FastAPI(
    title="Crate 中文电商智能客服",
    description="基于 LangGraph ReAct、Tool Calling 与 SQLite 的电商客服 Agent",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup():
    init_db()
    init_langfuse()


@app.on_event("shutdown")
def on_shutdown():
    """Flush any pending Langfuse traces before exit."""
    client = get_langfuse_client()
    if client:
        client.flush()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=settings.api_host, port=settings.api_port, reload=True)
