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


# ---------------------------------------------------------------------------
# Order tools
# ---------------------------------------------------------------------------

@tool
def lookup_order(order_id: str) -> str:
    """Look up an order by its ID (e.g. ORD-1001).
    Returns order details: items, status, total, tracking number, address.
    Use this when a customer asks about their order status."""
    order = order_service.get_order(order_id)
    if not order:
        return f"❌ Order #{order_id} not found. Please check your order number."

    items_str = "\n".join(
        f"  - {it.product_name} (SKU: {it.sku}) x{it.quantity} = ${it.price}"
        for it in order.items
    )
    return (
        f"📦 Order #{order.order_id}\n"
        f"👤 Customer: {order.customer_name}\n"
        f"📧 Email: {order.email}\n"
        f"📅 Date: {order.created_at[:10]}\n"
        f"📌 Status: {order.status}\n"
        f"💰 Total: ${order.total}\n"
        f"🏠 Address: {order.shipping_address}\n"
        f"📦 Tracking: {order.tracking_number or 'Not yet assigned'}\n"
        f"🛒 Items:\n{items_str}"
    )


@tool
def lookup_orders_by_email(email: str) -> str:
    """Find all orders associated with a customer email address.
    Use this when a customer asks 'what are my orders?' or gives their email."""
    orders = order_service.get_orders_by_email(email)
    if not orders:
        return f"❌ No orders found for {email}."

    lines = [f"📋 Orders for {email}:\n"]
    for o in orders:
        lines.append(
            f"  • #{o.order_id} — {o.status.upper()} — ${o.total} "
            f"({o.created_at[:10]})"
        )
    return "\n".join(lines)


@tool
def search_orders(query: str) -> str:
    """Search orders by customer name, product name, or partial order ID.
    Use this when a customer gives vague info like 'keyboard order' or 'John's order'."""
    orders = order_service.search_orders(query)
    if not orders:
        return f"❌ No orders found for '{query}'."

    lines = [f"🔍 Search results for '{query}' ({len(orders)} orders):\n"]
    for o in orders:
        items_preview = ", ".join(it.product_name for it in o.items[:2])
        if len(o.items) > 2:
            items_preview += f" +{len(o.items) - 2} more"
        lines.append(
            f"  • #{o.order_id} — {o.customer_name} — {o.status.upper()} — ${o.total}"
            f"\n    📦 {items_preview}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Shipping tools
# ---------------------------------------------------------------------------

@tool
def track_shipment(tracking_number: str) -> str:
    """Track a shipment by tracking number (e.g. FDX-78901234, UPS-45678901).
    Returns the current status and event history.
    Use this when a customer asks 'where is my package?' or provides a tracking number."""
    shipment = shipping_service.track(tracking_number)
    if not shipment:
        return f"❌ Tracking number {tracking_number} not found."

    events_str = "\n".join(
        f"  • {e.timestamp[:10]} — {e.location}: {e.description}"
        for e in shipment.events
    )
    status_emoji = {
        "delivered": "✅",
        "in_transit": "🚚",
        "out_for_delivery": "🏠",
        "label_created": "📦",
    }
    emoji = status_emoji.get(shipment.status, "📦")

    return (
        f"{emoji} **{shipment.carrier}** — {tracking_number}\n"
        f"📌 Status: {shipment.status.upper()}\n"
        f"📅 Estimated Delivery: {shipment.estimated_delivery}\n\n"
        f"📋 Tracking History:\n{events_str}"
    )


# ---------------------------------------------------------------------------
# Returns tools
# ---------------------------------------------------------------------------

@tool
def get_return_policy() -> str:
    """Get the store's return and refund policy.
    Use this when a customer asks about return conditions, refund timing,
    or what items can be returned."""
    return returns_service.get_policy()


@tool
def check_return_eligibility(order_id: str) -> str:
    """Check if an order is eligible for return.
    Use this BEFORE initiating a return, to verify the order can be returned."""
    can, message = order_service.can_return(order_id)
    if can:
        return f"✅ {message}"
    return f"❌ {message}"


@tool
def initiate_return(order_id: str, reason: str) -> str:
    """Start a return for an order. Requires order_id and a reason.
    Valid reasons: defective, wrong_item, not_as_described, changed_mind, damaged, too_late.
    Use this when a customer explicitly asks to return an order."""
    # Check eligibility first
    can, msg = order_service.can_return(order_id)
    if not can:
        return f"❌ Cannot initiate return: {msg}"

    order = order_service.get_order(order_id)
    ret = returns_service.create_return(order_id, reason, order.total)

    return (
        f"✅ Return request created!\n\n"
        f"📦 Order: #{ret.order_id}\n"
        f"🔢 RMA Number: **{ret.rma_number}**\n"
        f"💰 Refund Amount: ${ret.refund_amount}\n"
        f"📋 Reason: {reason}\n"
        f"📌 Status: Approved\n\n"
        f"⚠️ Your return shipping label will be sent to your email."
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
