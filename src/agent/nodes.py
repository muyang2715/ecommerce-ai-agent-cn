"""
LangGraph Nodes — the three processing stages of the ReAct agent.

  1. triage_node   → classify intent, extract entities
  2. tool_node     → execute the relevant backend tools (with retry)
  3. response_node → compose the final customer-facing reply
"""
import json
import re
import traceback

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from src.agent.state import AgentState
from src.agent.tools import ALL_TOOLS
from src.config import settings

# ---------------------------------------------------------------------------
# Shared LLM instance (lazy)
# ---------------------------------------------------------------------------

_llm = None
_llm_with_tools = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.temperature,
            api_key=settings.openai_api_key,
            max_retries=2,
        )
    return _llm


def _get_llm_with_tools():
    global _llm_with_tools
    if _llm_with_tools is None:
        _llm_with_tools = _get_llm().bind_tools(ALL_TOOLS)
    return _llm_with_tools

# ---------------------------------------------------------------------------
# 1. TRIAGE NODE
# ---------------------------------------------------------------------------

TRIAGE_PROMPT = """You are an e-commerce customer support triage assistant.
Analyze the customer's message and classify it as JSON:

{
    "intent": "<order_status | shipping_tracking | return_request | return_policy | general>",
    "order_id": "<order ID like ORD-1001, empty string if none>",
    "tracking_number": "<tracking number like FDX-78901234, empty string if none>",
    "customer_email": "<email address, empty string if none>",
    "needs_tool": true/false,
    "tool_name": "<best tool to call, empty if none>"
}

Rules:
- "order_status": customer is asking about their order
- "shipping_tracking": customer is asking about package tracking
- "return_request": customer wants to return an item
- "return_policy": customer is asking about return policy
- "general": greetings, thanks, chitchat

Return ONLY JSON, no other text."""


def triage_node(state: AgentState) -> dict:
    """Classify the user's intent and extract entities."""
    messages = state["messages"]

    last_user_msg = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content
            break

    if not last_user_msg:
        return {"intent": "general", "error_message": ""}

    try:
        response = _get_llm().invoke([
            SystemMessage(content=TRIAGE_PROMPT),
            HumanMessage(content=last_user_msg),
        ])

        content = response.content.strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        triage = json.loads(content)

        return {
            "intent": triage.get("intent", "general"),
            "order_id": triage.get("order_id", ""),
            "tracking_number": triage.get("tracking_number", ""),
            "customer_email": triage.get("customer_email", ""),
            "error_message": "",
        }

    except Exception:
        return {
            "intent": "general",
            "order_id": "",
            "tracking_number": "",
            "customer_email": "",
            "error_message": "",
        }


# ---------------------------------------------------------------------------
# 2. TOOL NODE (ReAct "Act" step with retry)
# ---------------------------------------------------------------------------

def tool_node(state: AgentState) -> dict:
    """Use LLM function-calling to decide and execute the right tool."""
    intent = state.get("intent", "general")
    messages = state.get("messages", [])
    retries = state.get("retry_count", 0)

    if intent == "general":
        return {"tool_results": {}, "retry_count": retries}

    context_prompt = f"""Customer intent: {intent}

Available context:
- Order ID: {state.get('order_id') or 'unknown'}
- Tracking Number: {state.get('tracking_number') or 'unknown'}
- Email: {state.get('customer_email') or 'unknown'}

Call the appropriate tool with the available parameters."""

    try:
        ai_msg = _get_llm_with_tools().invoke([
            SystemMessage(content=context_prompt),
            *messages,
        ])

        tool_results = {}

        if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
            for tc in ai_msg.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]

                for tool in ALL_TOOLS:
                    if tool.name == tool_name:
                        try:
                            result = tool.invoke(tool_args)
                            tool_results[tool_name] = str(result)
                        except Exception:
                            tool_results[tool_name] = (
                                f"❌ Error calling '{tool_name}': "
                                f"{traceback.format_exc()[-200:]}"
                            )
                        break
                else:
                    tool_results[tool_name] = f"❌ Tool '{tool_name}' not found."

        return {"tool_results": tool_results, "retry_count": retries + 1}

    except Exception as e:
        return {
            "tool_results": {"error": str(e)},
            "retry_count": retries + 1,
            "error_message": str(e),
        }


# ---------------------------------------------------------------------------
# 3. RESPONSE NODE
# ---------------------------------------------------------------------------

RESPONSE_PROMPT = """LANGUAGE: You are an English-only customer support agent. Write ONLY in English. Turkish is FORBIDDEN.

Compose a friendly, structured response using the information below.

Customer Intent: {intent}
Tool Results: {tool_results}

Guidelines:
- WRITE IN ENGLISH. Do not use any other language.
- Use the exact data from tool results, do not fabricate.
- Format with bullet points.
- Include order IDs and tracking numbers.
- End with: "Is there anything else I can help you with?"
- If no tools were used, introduce yourself in English and list what you can help with."""


def response_node(state: AgentState) -> dict:
    """Compose the final customer-facing response."""
    intent = state.get("intent", "general")
    tool_results = state.get("tool_results", {})
    messages = state.get("messages", [])
    error = state.get("error_message", "")

    # -- Fallback on persistent error --
    if error and not tool_results:
        return {
            "final_response": (
                "I apologize, but I'm having trouble processing your request right now. "
                "Please try again in a moment, or contact our support team directly at "
                "support@crate.ai. Is there anything else I can help you with?"
            )
        }

    # -- General / greeting --
    if intent == "general" and not tool_results:
        return {
            "final_response": (
                "Hello! 👋 I'm Crate's virtual assistant. I can help you with:\n\n"
                "📦 **Order Status** — Check your order with your order ID.\n"
                "🚚 **Package Tracking** — Track your shipment with your tracking number.\n"
                "🔄 **Returns** — Learn about our return policy or initiate a return.\n\n"
                "How can I help you today?"
            )
        }

    # -- Compose from tool results --
    try:
        formatted_prompt = RESPONSE_PROMPT.format(
            intent=intent,
            tool_results=json.dumps(tool_results, ensure_ascii=False, indent=2),
        )

        response = _get_llm().invoke([
            SystemMessage(content=formatted_prompt),
            *messages,
        ])

        text = response.content.strip()

        # If Turkish leaked through, use raw English tool results directly
        if _contains_turkish(text) and tool_results:
            text = _format_tool_results(intent, tool_results)

        return {"final_response": text}

    except Exception:
        parts = []
        for tool_name, result in tool_results.items():
            parts.append(f"**{tool_name}** result:\n{result}")
        return {"final_response": "\n\n".join(parts)}


def _contains_turkish(text: str) -> bool:
    """Detect if text contains Turkish-specific characters or common Turkish words."""
    turkish_chars = set("ğıİşŞçÇöÖüÜĞ")
    turkish_words = [
        "merhaba", "sipariş", "siparişiniz", "kargonuz", "takip",
        "teslimat", "ürün", "ürünler", "bulabilirsiniz", "teşekkür",
        "yardımcı", "memnuniyetle", "lütfen", "gönderinizi",
    ]
    lower = text.lower()
    if any(c in text for c in turkish_chars):
        return True
    if any(w in lower for w in turkish_words):
        return True
    return False


def _format_tool_results(intent: str, tool_results: dict) -> str:
    """Format raw tool results into a clean English response without LLM."""
    parts = []
    if intent == "order_status":
        parts.append("Here are your order details:\n")
    elif intent == "shipping_tracking":
        parts.append("Here is your shipment status:\n")
    elif intent == "return_request":
        parts.append("Here is your return request status:\n")
    elif intent == "return_policy":
        parts.append("Here is our return policy:\n")
    else:
        parts.append("Here is what I found:\n")

    for result in tool_results.values():
        parts.append(str(result))

    parts.append("\nIs there anything else I can help you with?")
    return "\n".join(parts)
