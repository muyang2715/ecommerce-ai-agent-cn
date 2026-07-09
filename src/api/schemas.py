"""
Pydantic schemas for the FastAPI gateway.
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="Kullanıcının mesajı", min_length=1)
    session_id: str = Field(default="default", description="Oturum ID'si (çoklu konuşma için)")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Asistanın yanıtı")
    intent: str = Field(default="general", description="Tespit edilen amaç")
    order_id: str = Field(default="", description="Çıkarılan sipariş numarası")
    tracking_number: str = Field(default="", description="Çıkarılan kargo takip no")
    customer_email: str = Field(default="", description="Çıkarılan e-posta")
    tool_results: dict = Field(default_factory=dict, description="Araç çağrı sonuçları")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
