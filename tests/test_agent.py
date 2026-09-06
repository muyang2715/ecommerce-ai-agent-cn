"""
Unit & Integration tests for the E-Commerce Support Agent.
"""
import pytest
from src.services.database import init_db


@pytest.fixture(scope="module", autouse=True)
def _setup_database():
    """Initialize the SQLite database once before all tests."""
    init_db()


# ---------------------------------------------------------------------------
# Service tests (no LLM needed)
# ---------------------------------------------------------------------------


class TestOrderService:
    def test_get_existing_order(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        order = svc.get_order("ORD-1001")
        assert order is not None
        assert order.customer_name == "James Wilson"
        assert order.status == "delivered"
        assert len(order.items) == 2

    def test_get_missing_order(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        order = svc.get_order("ORD-9999")
        assert order is None

    def test_get_orders_by_email(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        orders = svc.get_orders_by_email("james@example.com")
        assert len(orders) >= 1
        assert any(o.order_id == "ORD-1001" for o in orders)

    def test_get_orders_by_email_multiple(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        orders = svc.get_orders_by_email("james@example.com")
        assert len(orders) == 2

    def test_search_orders_by_name(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        results = svc.search_orders("James")
        assert len(results) >= 2

    def test_search_orders_by_product(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        results = svc.search_orders("Headphones")
        assert len(results) >= 1

    def test_get_all_orders(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        orders = svc.get_all_orders()
        assert len(orders) == 12

    def test_can_return_delivered_order(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        can, msg = svc.can_return("ORD-1001")
        assert can is True

    def test_cannot_return_cancelled_order(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        can, msg = svc.can_return("ORD-1004")
        assert can is False
        assert "取消" in msg

    def test_cannot_return_unshipped_order(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        can, msg = svc.can_return("ORD-1003")
        assert can is False

    def test_cannot_return_expired_order(self):
        from src.services.order_service import OrderService

        svc = OrderService()
        can, msg = svc.can_return("ORD-1008")
        assert can is False
        assert "14" in msg


class TestShippingService:
    def test_track_existing(self):
        from src.services.shipping_service import ShippingService

        svc = ShippingService()
        shipment = svc.track("FDX-78901234")
        assert shipment is not None
        assert shipment.carrier == "FedEx"
        assert shipment.status == "delivered"

    def test_track_missing(self):
        from src.services.shipping_service import ShippingService

        svc = ShippingService()
        shipment = svc.track("XXX-00000000")
        assert shipment is None

    def test_readable_status(self):
        from src.services.shipping_service import ShippingService

        svc = ShippingService()
        status = svc.get_readable_status("FDX-78901234")
        assert "已送达" in status


class TestReturnsService:
    def test_create_return(self):
        from src.services.returns_service import ReturnsService

        svc = ReturnsService()
        ret = svc.create_return("ORD-1001", "defective", 105.97)
        assert ret.rma_number.startswith("RMA-")
        assert ret.status == "approved"
        assert ret.refund_amount == 105.97

    def test_get_policy(self):
        from src.services.returns_service import ReturnsService

        svc = ReturnsService()
        policy = svc.get_policy()
        assert "14 天" in policy


class TestProductService:
    def test_search_products_by_chinese_keyword(self):
        from src.services.product_service import ProductService

        svc = ProductService()
        products = svc.search_products(query="键盘")
        assert len(products) == 1
        assert products[0].product_name == "Mechanical Keyboard"

    def test_search_products_by_budget(self):
        from src.services.product_service import ProductService

        svc = ProductService()
        products = svc.search_products(max_price=30)
        assert products
        assert all(product.price <= 30 for product in products)

    def test_search_products_with_natural_chinese_phrase(self):
        from src.services.product_service import ProductService

        svc = ProductService()
        products = svc.search_products(
            query="办公键盘",
            category="办公用品",
            max_price=150,
        )
        assert products
        assert products[0].product_name == "Mechanical Keyboard"


# ---------------------------------------------------------------------------
# Agent tool tests (no LLM needed)
# ---------------------------------------------------------------------------


class TestAgentTools:
    def test_lookup_order(self):
        from src.agent.tools import lookup_order

        result = lookup_order.invoke({"order_id": "ORD-1001"})
        assert "James Wilson" in result
        assert "已送达" in result
        assert "105.97" in result

    def test_lookup_missing_order(self):
        from src.agent.tools import lookup_order

        result = lookup_order.invoke({"order_id": "ORD-XXXX"})
        assert "未找到" in result

    def test_track_shipment(self):
        from src.agent.tools import track_shipment

        result = track_shipment.invoke({"tracking_number": "UPS-45678901"})
        assert "UPS" in result
        assert "运输中" in result

    def test_get_return_policy(self):
        from src.agent.tools import get_return_policy

        result = get_return_policy.invoke({})
        assert "14 天" in result

    def test_check_return_eligibility(self):
        from src.agent.tools import check_return_eligibility

        result = check_return_eligibility.invoke({"order_id": "ORD-1001"})
        assert "✅" in result

    def test_search_product_catalog(self):
        from src.agent.tools import search_product_catalog

        result = search_product_catalog.invoke({"query": "键盘", "max_price": 150})
        assert "Mechanical Keyboard" in result
        assert "$149.99" in result


# ---------------------------------------------------------------------------
# Graph structure test (no LLM needed)
# ---------------------------------------------------------------------------


class TestGraph:
    def test_graph_builds(self):
        from src.agent.graph import build_graph

        graph = build_graph()
        assert graph is not None

    def test_graph_has_nodes(self):
        from src.agent.graph import build_graph

        graph = build_graph()
        nodes = graph.get_graph().nodes
        assert "triage" in nodes
        assert "tools" in nodes
        assert "response" in nodes

    def test_should_use_tools_logic(self):
        from src.agent.graph import should_use_tools

        assert should_use_tools({"intent": "order_status"}) == "tools"
        assert should_use_tools({"intent": "shipping_tracking"}) == "tools"
        assert should_use_tools({"intent": "return_request"}) == "tools"
        assert should_use_tools({"intent": "general"}) == "response"
        assert should_use_tools({"intent": "return_policy"}) == "tools"
        assert should_use_tools({"intent": "product_discovery"}) == "tools"
