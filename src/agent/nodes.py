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
            base_url=settings.openai_base_url or None,
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

TRIAGE_PROMPT = """你是一名电商客服分流助手。
请分析客户的中文或英文消息，并严格输出以下 JSON：

{
    "intent": "<order_status | shipping_tracking | return_request | return_policy | general>",
    "order_id": "<订单号，例如 ORD-1001；没有则为空字符串>",
    "tracking_number": "<物流单号，例如 FDX-78901234；没有则为空字符串>",
    "customer_email": "<客户邮箱；没有则为空字符串>",
    "needs_tool": true/false,
    "tool_name": "<best tool to call, empty if none>"
}

分类规则：
- "order_status"：客户查询订单、本人订单或按商品搜索订单
- "shipping_tracking"：客户查询包裹或物流轨迹
- "return_request"：客户希望退货或查询某个订单能否退货
- "return_policy"：客户询问退货规则、期限或退款政策
- "general"：问候、感谢或闲聊

只返回 JSON，不要添加 Markdown 或说明文字。"""


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

    context_prompt = f"""客户意图：{intent}

可用信息：
- 订单号：{state.get('order_id') or '未知'}
- 物流单号：{state.get('tracking_number') or '未知'}
- 客户邮箱：{state.get('customer_email') or '未知'}

请根据客户消息和以上信息调用最合适的工具。不要编造缺失参数。"""

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
                                f"❌ 调用工具“{tool_name}”失败："
                                f"{traceback.format_exc()[-200:]}"
                            )
                        break
                else:
                    tool_results[tool_name] = f"❌ 未找到工具“{tool_name}”。"

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

RESPONSE_PROMPT = """你是 Crate 的中文电商客服。必须使用简体中文回复。

请根据以下信息生成友好、清晰、简洁的客户回复。

客户意图：{intent}
工具结果：{tool_results}

要求：
- 使用自然、专业的简体中文，不要整段输出英文。
- 只使用工具结果中真实存在的数据，不得编造。
- 订单号、物流单号、SKU、姓名、地址和商品原名可以保留原文。
- 日期必须原样引用，不要自行推断“今天”“明天”或“几天后”。
- 信息较多时使用项目符号，避免冗长套话。
- 结尾使用：“还有什么可以帮您的吗？”
- 没有调用工具时，简短介绍可以提供的订单、物流和退货帮助。"""


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
                "抱歉，当前暂时无法处理您的请求。请稍后重试，"
                "或联系 support@crate.ai 获取人工帮助。还有什么可以帮您的吗？"
            )
        }

    # -- General / greeting --
    if intent == "general" and not tool_results:
        return {
            "final_response": (
                "您好，我是 Crate 智能客服。\n\n"
                "我可以帮您：\n"
                "- 📦 查询订单状态\n"
                "- 🚚 追踪包裹物流\n"
                "- ↩️ 了解退货政策或判断退货资格\n\n"
                "请告诉我您想查询什么。"
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

        # 兼容部分 OpenAI-compatible 模型泄漏的工具标记。
        if tool_results and "<tool_call>" in text.lower():
            text = _format_tool_results(intent, tool_results)

        return {"final_response": text}

    except Exception:
        parts = []
        for tool_name, result in tool_results.items():
            parts.append(f"**{tool_name}** 查询结果：\n{result}")
        return {"final_response": "\n\n".join(parts)}


def _format_tool_results(intent: str, tool_results: dict) -> str:
    """无需 LLM，将已验证的工具结果整理为中文回复。"""
    parts = []
    if intent == "order_status":
        parts.append("这是为您查询到的订单信息：\n")
    elif intent == "shipping_tracking":
        parts.append("这是为您查询到的物流信息：\n")
    elif intent == "return_request":
        parts.append("这是该订单的退货查询结果：\n")
    elif intent == "return_policy":
        parts.append("这是 Crate 的退货政策：\n")
    else:
        parts.append("这是为您查询到的信息：\n")

    for result in tool_results.values():
        parts.append(str(result))

    parts.append("\n还有什么可以帮您的吗？")
    return "\n".join(parts)
