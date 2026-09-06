"""商品目录服务——为智能导购提供可检索的 SQLite 数据。"""

import re
from dataclasses import dataclass
from typing import Optional

from src.services.database import get_connection


@dataclass
class Product:
    product_id: str
    product_name: str
    category: str
    price: float
    description: str
    keywords: str
    in_stock: bool


def _row_to_product(row) -> Product:
    return Product(
        product_id=row["product_id"],
        product_name=row["product_name"],
        category=row["category"],
        price=row["price"],
        description=row["description"],
        keywords=row["keywords"],
        in_stock=bool(row["in_stock"]),
    )


class ProductService:
    """提供商品浏览、关键词检索和预算筛选。"""

    def search_products(
        self,
        query: str = "",
        category: str = "",
        max_price: Optional[float] = None,
        limit: int = 8,
    ) -> list[Product]:
        clauses = ["in_stock = 1"]
        params: list[object] = []

        if max_price is not None:
            clauses.append("price <= ?")
            params.append(max_price)

        sql = (
            "SELECT * FROM products WHERE "
            + " AND ".join(clauses)
            + " ORDER BY price ASC"
        )

        conn = get_connection()
        try:
            rows = conn.execute(sql, params).fetchall()
            products = [_row_to_product(row) for row in rows]
        finally:
            conn.close()

        search_text = " ".join(part for part in (query, category) if part.strip())
        tokens = _search_tokens(search_text)
        if not tokens:
            return products[:max(1, min(limit, 20))]

        ranked = []
        for product in products:
            haystack = " ".join(
                [
                    product.product_name,
                    product.category,
                    product.description,
                    product.keywords,
                ]
            ).lower()
            matched_tokens = {token for token in tokens if token in haystack}
            if matched_tokens:
                ranked.append((len(matched_tokens), product))

        ranked.sort(key=lambda item: (-item[0], item[1].price))
        return [product for _, product in ranked[:max(1, min(limit, 20))]]


def _search_tokens(value: str) -> set[str]:
    """把中英文自然语言查询转换成适合小型目录的关键词。"""
    normalized = value.strip().lower()
    if not normalized:
        return set()

    tokens = set(re.findall(r"[a-z0-9][a-z0-9-]+", normalized))
    for segment in re.findall(r"[\u4e00-\u9fff]+", normalized):
        if len(segment) <= 2:
            tokens.add(segment)
        else:
            tokens.update(segment[index:index + 2] for index in range(len(segment) - 1))
    return {token for token in tokens if len(token) >= 2}
