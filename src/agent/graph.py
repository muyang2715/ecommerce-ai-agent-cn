"""
LangGraph Graph — Production-grade ReAct agent with retry loop.

Flow:
  START → triage_node ─┬─(needs tools)→ tool_node ─┬─(success)→ response_node → END
                        │                          │
                        │                          └─(retryable error, retries < 3)→ tool_node
                        │
                        └─(general / no tools)→ response_node → END
"""
from langgraph.graph import END, StateGraph

from src.agent.state import AgentState
from src.agent.nodes import triage_node, tool_node, response_node

MAX_RETRIES = 3


def should_use_tools(state: AgentState) -> str:
    """Router after triage: decide whether to call tools or respond directly."""
    intent = state.get("intent", "general")
    if intent in ("general",):
        return "response"
    return "tools"


def after_tools(state: AgentState) -> str:
    """Router after tools: check for errors, retry if possible."""
    tool_results = state.get("tool_results", {})

    # Check if any tool returned an error
    has_error = any(
        str(v).startswith("❌") or "error" in str(v).lower()
        for v in tool_results.values()
    )

    retries = state.get("retry_count", 0)

    if has_error and retries < MAX_RETRIES:
        return "retry"
    return "response"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph state graph with retry loop."""

    workflow = StateGraph(AgentState)

    # -- Add nodes --
    workflow.add_node("triage", triage_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("response", response_node)

    # -- Add edges --
    workflow.set_entry_point("triage")

    # Triage → tools or response
    workflow.add_conditional_edges(
        "triage",
        should_use_tools,
        {"tools": "tools", "response": "response"},
    )

    # Tools → response or retry
    workflow.add_conditional_edges(
        "tools",
        after_tools,
        {"retry": "tools", "response": "response"},
    )

    # Response → END
    workflow.add_edge("response", END)

    return workflow.compile()


# Singleton compiled graph
agent_graph = build_graph()
