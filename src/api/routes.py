"""
FastAPI Routes — the Agent Gateway.
"""
from fastapi import APIRouter

from src.agent.graph import agent_graph
from src.agent.state import AgentState
from src.api.schemas import ChatRequest, ChatResponse, HealthResponse
from src.observability.langfuse_setup import get_langfuse_client, get_langfuse_handler
from langchain_core.messages import HumanMessage, SystemMessage

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Main chat endpoint: runs the full ReAct agent graph."""

    initial_state: AgentState = {
        "messages": [
            SystemMessage(content=(
                "IMPORTANT LANGUAGE RULE: You are an English-only assistant. "
                "You MUST write all responses in English. Do NOT use Turkish, "
                "even if the customer writes in Turkish. Always reply in English."
            )),
            HumanMessage(content=req.message),
        ],
        "intent": "",
        "order_id": "",
        "tracking_number": "",
        "customer_email": "",
        "tool_results": {},
        "final_response": "",
        "retry_count": 0,
        "error_message": "",
    }

    # Build invoke config with Langfuse callback
    invoke_config = {}
    handler = get_langfuse_handler()
    if handler:
        invoke_config["callbacks"] = [handler]

    # Run the graph
    result = agent_graph.invoke(initial_state, invoke_config)

    # Flush traces to Langfuse
    client = get_langfuse_client()
    if client:
        client.flush()

    return ChatResponse(
        response=result.get("final_response", "Sorry, something went wrong."),
        intent=result.get("intent", "general"),
        order_id=result.get("order_id", ""),
        tracking_number=result.get("tracking_number", ""),
        customer_email=result.get("customer_email", ""),
        tool_results=result.get("tool_results", {}),
    )
