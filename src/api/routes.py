"""
FastAPI Routes — the Agent Gateway.
"""
from threading import Lock

from fastapi import APIRouter

from src.agent.graph import agent_graph
from src.agent.state import AgentState
from src.api.schemas import ChatRequest, ChatResponse, HealthResponse
from src.observability.langfuse_setup import get_langfuse_client, get_langfuse_handler
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

router = APIRouter()

_session_history: dict[str, list] = {}
_session_lock = Lock()
MAX_HISTORY_MESSAGES = 12
MAX_SESSIONS = 100


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Main chat endpoint: runs the full ReAct agent graph."""

    with _session_lock:
        history = list(_session_history.get(req.session_id, []))

    initial_state: AgentState = {
        "messages": [
            SystemMessage(content=(
                "重要语言规则：你是 Crate 中文品牌智能助手。无论客户使用中文还是英文，"
                "都使用简体中文回复；既能自然交流，也会在需要时调用电商业务工具。"
                "订单号、物流单号、SKU、姓名和地址可保留原文。"
            )),
            *history,
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

    final_response = result.get("final_response", "抱歉，系统暂时无法处理您的请求。")

    with _session_lock:
        if req.session_id not in _session_history and len(_session_history) >= MAX_SESSIONS:
            oldest_session = next(iter(_session_history))
            _session_history.pop(oldest_session, None)
        _session_history[req.session_id] = [
            *history,
            HumanMessage(content=req.message),
            AIMessage(content=final_response),
        ][-MAX_HISTORY_MESSAGES:]

    return ChatResponse(
        response=final_response,
        intent=result.get("intent", "general"),
        order_id=result.get("order_id", ""),
        tracking_number=result.get("tracking_number", ""),
        customer_email=result.get("customer_email", ""),
        tool_results=result.get("tool_results", {}),
    )
