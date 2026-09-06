"""
Tool Definitions — the functions the agent can call to interact with backend systems.

Uses LangChain's @tool decorator so they are automatically exposed as
OpenAI function-calling tools.
"""
from langchain_core.tools import tool

from src.services.order_service import OrderService
from src.services.shipping_service import ShippingService
from src.services.returns_service import ReturnsService

# Singleton service instances
order_service = OrderService()
shipping_service = ShippingService()
returns_service = ReturnsService()

ORDER_STATUS_LABELS = {
    "confirmed": "已确认",
    "shipped": "已发货",
    "delivered": "已送达",
    "cancelled": "已取消",
}

SHIPMENT_STATUS_LABELS = {
    "label_created": "运单已创建",
    "in_transit": "运输中",
    "out_for_delivery": "派送中",
    "delivered": "已送达",
}

EVENT_DESCRIPTION_LABELS = {
    "Package picked up": "包裹已由承运商揽收",
    "Arrived at FedEx hub": "已到达 FedEx 转运中心",
    "Out for delivery": "正在派送",
    "Delivered": "已送达",
    "Processing at UPS facility": "正在 UPS 处理中心处理",
    "International transit hub": "已到达国际转运中心",
    "Arrived at local facility": "已到达本地处理中心",
}


# ---------------------------------------------------------------------------
# Order tools
# ---------------------------------------------------------------------------

@tool
def lookup_order(order_id: str) -> str:
    """按订单号（例如 ORD-1001）查询订单详情，包括商品、状态、金额、物流单号和收货地址。"""
    order = order_service.get_order(order_id)
    if not order:
        return f"❌ 未找到订单 #{order_id}，请检查订单号是否正确。"

    items_str = "\n".join(
        f"  - {it.product_name}（SKU：{it.sku}）× {it.quantity}，${it.price}"
        for it in order.items
    )
    status = ORDER_STATUS_LABELS.get(order.status, order.status)
    return (
        f"📦 订单 #{order.order_id}\n"
        f"👤 客户：{order.customer_name}\n"
        f"📧 邮箱：{order.email}\n"
        f"📅 下单日期：{order.created_at[:10]}\n"
        f"📌 状态：{status}\n"
        f"💰 订单金额：${order.total}\n"
        f"🏠 收货地址：{order.shipping_address}\n"
        f"🚚 物流单号：{order.tracking_number or '尚未分配'}\n"
        f"🛒 商品：\n{items_str}"
    )


@tool
def lookup_orders_by_email(email: str) -> str:
    """根据客户邮箱查询其全部订单。适用于“查看我的订单”等请求。"""
    orders = order_service.get_orders_by_email(email)
    if not orders:
        return f"❌ 未找到与 {email} 关联的订单。"

    lines = [f"📋 {email} 的订单：\n"]
    for o in orders:
        status = ORDER_STATUS_LABELS.get(o.status, o.status)
        lines.append(
            f"  • #{o.order_id} — {status} — ${o.total} "
            f"（{o.created_at[:10]}）"
        )
    return "\n".join(lines)


@tool
def search_orders(query: str) -> str:
    """按客户姓名、商品名称或部分订单号模糊搜索订单。"""
    orders = order_service.search_orders(query)
    if not orders:
        return f"❌ 未找到与“{query}”相关的订单。"

    lines = [f"🔍 “{query}”的搜索结果（{len(orders)} 个订单）：\n"]
    for o in orders:
        items_preview = ", ".join(it.product_name for it in o.items[:2])
        if len(o.items) > 2:
            items_preview += f"，另有 {len(o.items) - 2} 件"
        status = ORDER_STATUS_LABELS.get(o.status, o.status)
        lines.append(
            f"  • #{o.order_id} — {o.customer_name} — {status} — ${o.total}"
            f"\n    🛒 {items_preview}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Shipping tools
# ---------------------------------------------------------------------------

@tool
def track_shipment(tracking_number: str) -> str:
    """按物流单号查询承运商、当前状态、预计送达时间和物流轨迹。"""
    shipment = shipping_service.track(tracking_number)
    if not shipment:
        return f"❌ 未找到物流单号 {tracking_number}。"

    events_str = "\n".join(
        f"  • {e.timestamp[:10]} — {e.location}："
        f"{EVENT_DESCRIPTION_LABELS.get(e.description, e.description)}"
        for e in shipment.events
    )
    status_emoji = {
        "delivered": "✅",
        "in_transit": "🚚",
        "out_for_delivery": "🏠",
        "label_created": "📦",
    }
    emoji = status_emoji.get(shipment.status, "📦")
    status = SHIPMENT_STATUS_LABELS.get(shipment.status, shipment.status)

    return (
        f"{emoji} **{shipment.carrier}** — {tracking_number}\n"
        f"📌 物流状态：{status}\n"
        f"📅 预计送达：{shipment.estimated_delivery}\n\n"
        f"📋 物流轨迹：\n{events_str}"
    )


# ---------------------------------------------------------------------------
# Returns tools
# ---------------------------------------------------------------------------

@tool
def get_return_policy() -> str:
    """查询商店的退货和退款政策，包括期限、运费和不可退商品。"""
    return returns_service.get_policy()


@tool
def check_return_eligibility(order_id: str) -> str:
    """检查订单是否符合退货条件。发起退货前应先调用此工具。"""
    can, message = order_service.can_return(order_id)
    if can:
        return f"✅ {message}"
    return f"❌ {message}"


@tool
def initiate_return(order_id: str, reason: str) -> str:
    """为订单创建退货申请，需要订单号和原因。
    原因可选：defective、wrong_item、not_as_described、changed_mind、damaged、too_late。"""
    # Check eligibility first
    can, msg = order_service.can_return(order_id)
    if not can:
        return f"❌ 无法发起退货：{msg}"

    order = order_service.get_order(order_id)
    ret = returns_service.create_return(order_id, reason, order.total)

    return (
        f"✅ 退货申请已创建！\n\n"
        f"📦 订单：#{ret.order_id}\n"
        f"🔢 退货编号：**{ret.rma_number}**\n"
        f"💰 退款金额：${ret.refund_amount}\n"
        f"📋 退货原因：{reason}\n"
        f"📌 状态：已批准\n\n"
        f"⚠️ 退货运单将发送至您的邮箱。"
    )


# ---------------------------------------------------------------------------
# Aggregate tool list
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    lookup_order,
    lookup_orders_by_email,
    search_orders,
    track_shipment,
    get_return_policy,
    check_return_eligibility,
    initiate_return,
]
