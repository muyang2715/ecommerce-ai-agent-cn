"""
Order Service — SQLite-backed order management.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from src.services.database import get_connection


@dataclass
class OrderItem:
    product_name: str
    sku: str
    quantity: int
    price: float


@dataclass
class Order:
    order_id: str
    customer_name: str
    email: str
    items: list[OrderItem]
    status: str  # confirmed, shipped, delivered, cancelled
    total: float
    created_at: str
    shipping_address: str
    tracking_number: Optional[str] = None


def _row_to_order(row) -> Order:
    items = [OrderItem(**i) for i in json.loads(row["items"])]
    return Order(
        order_id=row["order_id"],
        customer_name=row["customer_name"],
        email=row["email"],
        items=items,
        status=row["status"],
        total=row["total"],
        created_at=row["created_at"],
        shipping_address=row["shipping_address"],
        tracking_number=row["tracking_number"],
    )


class OrderService:
    """SQLite-backed order management."""

    def get_order(self, order_id: str) -> Optional[Order]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM orders WHERE order_id = ?", (order_id.upper(),)
            ).fetchone()
            return _row_to_order(row) if row else None
        finally:
            conn.close()

    def get_orders_by_email(self, email: str) -> list[Order]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM orders WHERE email = ? ORDER BY created_at DESC",
                (email.lower(),),
            ).fetchall()
            return [_row_to_order(r) for r in rows]
        finally:
            conn.close()

    def get_all_orders(self) -> list[Order]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM orders ORDER BY created_at DESC"
            ).fetchall()
            return [_row_to_order(r) for r in rows]
        finally:
            conn.close()

    def search_orders(self, query: str) -> list[Order]:
        """Search by order ID, customer name, or product name."""
        conn = get_connection()
        try:
            pattern = f"%{query}%"
            rows = conn.execute(
                """SELECT DISTINCT o.* FROM orders o
                   WHERE o.order_id LIKE ?
                      OR o.customer_name LIKE ?
                      OR o.items LIKE ?
                   ORDER BY o.created_at DESC""",
                (pattern, pattern, pattern),
            ).fetchall()
            return [_row_to_order(r) for r in rows]
        finally:
            conn.close()

    def can_return(self, order_id: str) -> tuple[bool, str]:
        """判断订单是否已送达且仍在 14 天退货期内。"""
        order = self.get_order(order_id)
        if not order:
            return False, f"未找到订单 {order_id}。"
        if order.status == "cancelled":
            return False, "已取消的订单不能申请退货。"
        if order.status != "delivered":
            return False, f"订单尚未送达（当前状态：{order.status}）。"
        created = datetime.fromisoformat(order.created_at)
        if datetime.now() - created > timedelta(days=14):
            return False, "该订单已超过 14 天退货期限。"
        return True, "该订单符合退货条件。"
