"""
Shipping Service — SQLite-backed carrier tracking.
"""
import json
from dataclasses import dataclass
from typing import Optional

from src.services.database import get_connection


@dataclass
class TrackingEvent:
    timestamp: str
    location: str
    description: str


@dataclass
class Shipment:
    tracking_number: str
    carrier: str
    status: str  # label_created, in_transit, out_for_delivery, delivered
    estimated_delivery: str
    events: list[TrackingEvent]


STATUS_LABELS = {
    "label_created": "📦 运单已创建，包裹尚未交给承运商。",
    "in_transit": "🚚 包裹正在运输途中。",
    "out_for_delivery": "🏠 包裹正在派送，预计今天送达。",
    "delivered": "✅ 包裹已送达。",
}


def _row_to_shipment(row) -> Shipment:
    events = [TrackingEvent(**e) for e in json.loads(row["events"])]
    return Shipment(
        tracking_number=row["tracking_number"],
        carrier=row["carrier"],
        status=row["status"],
        estimated_delivery=row["estimated_delivery"] or "",
        events=events,
    )


class ShippingService:
    """SQLite-backed shipping tracking."""

    def track(self, tracking_number: str) -> Optional[Shipment]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM shipments WHERE tracking_number = ?",
                (tracking_number.upper(),),
            ).fetchone()
            return _row_to_shipment(row) if row else None
        finally:
            conn.close()

    def get_readable_status(self, tracking_number: str) -> str:
        shipment = self.track(tracking_number)
        if not shipment:
            return f"❌ 未找到物流单号 {tracking_number}。"
        return STATUS_LABELS.get(shipment.status, f"物流状态：{shipment.status}")
