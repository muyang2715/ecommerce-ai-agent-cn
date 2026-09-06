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
    "intent": "<order_status | shipping_tracking | return_request | return_policy | product_discovery | general>",
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
- "product_discovery"：商品浏览、购买建议、商品比较、用途推荐或预算筛选
- "general"：问候、感谢、闲聊，以及不需要订单或商品数据库的知识问题

如果当前消息是“便宜一点呢”“那它能退吗”等追问，请结合最近对话判断真实意图并提取可用信息。

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
        recent_conversation = [
            message
            for message in messages
            if isinstance(message, (HumanMessage, AIMessage))
        ][-8:]
        response = _get_llm().invoke([
            SystemMessage(content=TRIAGE_PROMPT),
            *recent_conversation,
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

RESPONSE_PROMPT = """你是 Crate 的中文品牌智能助手，交流方式自然、主动、有帮助。

你的业务范围包括电商导购、商品比较、订单售后、物流、退货，以及用户提出的一般知识问题。请根据客户当前问题直接作答，不要机械重复固定的能力菜单。

客户意图：{intent}
工具结果：{tool_results}

要求：
- 使用自然、专业的简体中文，不要整段输出英文。
- 有工具结果时，只使用结果中真实存在的业务数据，不得编造订单、商品、价格、库存、优惠或物流状态。
- 没有工具结果时，可使用通用知识直接回答问题；若问题需要 Crate 的实时商品、库存、优惠、门店或支付数据，应说明尚未接入对应数据。
- product_discovery 应结合商品结果和用户需求给出 1～3 个有理由的建议，而不是简单复述列表。
- 商品推荐理由只能基于工具返回的价格、品类和描述；不得补充轴体、材质、功能、门店或其他未返回的信息。
- 如果工具没有找到商品，只说明本地目录没有匹配结果，并询问用户愿意放宽哪个条件；不要猜测缺货原因或推荐未返回的渠道。
- 当前导购只能查询和推荐商品，尚未接入购物车、支付和新订单创建；不得声称可以替用户下单或完成付款。
- 不得声称 Crate 存在官网、App、线下门店或其他购买渠道；需要购买时，只说明应在用户实际使用的购买渠道完成。
- 订单号、物流单号、SKU、姓名、地址和商品原名可以保留原文。
- 日期必须原样引用，不要自行推断“今天”“明天”或“几天后”。
- 信息较多时使用项目符号，避免冗长套话。
- 根据语境自然收尾，不要每次使用相同句式。"""


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
        if not tool_results:
            return {
                "final_response": (
                    "抱歉，智能助手暂时无法连接模型服务，请稍后再试。"
                )
            }
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
    elif intent == "product_discovery":
        parts.append("这是根据您需求筛选出的商品：\n")
    else:
        parts.append("这是为您查询到的信息：\n")

    for result in tool_results.values():
        parts.append(str(result))

    parts.append("\n还有什么可以帮您的吗？")
    return "\n".join(parts)
