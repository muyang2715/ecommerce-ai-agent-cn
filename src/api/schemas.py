"""
Pydantic schemas for the FastAPI gateway.
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息", min_length=1)
    session_id: str = Field(default="default", description="会话 ID（预留用于多轮会话）")


class ChatResponse(BaseModel):
    response: str = Field(..., description="客服回复")
    intent: str = Field(default="general", description="识别出的用户意图")
    order_id: str = Field(default="", description="提取出的订单号")
    tracking_number: str = Field(default="", description="提取出的物流单号")
    customer_email: str = Field(default="", description="提取出的客户邮箱")
    tool_results: dict = Field(default_factory=dict, description="工具调用结果")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
