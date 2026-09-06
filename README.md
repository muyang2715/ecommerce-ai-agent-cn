# Crate 中文电商品牌智能助手

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-green.svg)](https://langchain.com/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-28%20passed-brightgreen.svg)](tests/)

这是 [m-peker/ecommerce-ai-agent](https://github.com/m-peker/ecommerce-ai-agent) 的中文本地复现与扩展版本。项目保留原作者、Git 历史与 MIT License；在保留订单、物流和退货逻辑的基础上，增加了开放式对话、SQLite 商品目录、智能导购、多轮上下文和 Claude 风格界面。

> 当前定位：可本地演示的电商品牌 Agent。一般问题由模型直接回答，需要业务数据时由模型自主选择 Tool。

## 项目能力

- 按订单号查询状态、金额、商品、地址和物流单号
- 按邮箱列出客户订单，或按商品名模糊搜索订单
- 按物流单号查询承运商、状态、预计送达日期和轨迹
- 查询退货政策、检查订单退货资格、创建 RMA
- 浏览商品目录，按用途、品类和预算给出购买建议
- 回答一般知识问题，不再为 `general` 返回写死的能力菜单
- 使用 `session_id` 保存最近 12 条消息，理解“便宜一点呢”等追问
- LangGraph 三节点工作流、LLM Tool Calling 和错误重试
- FastAPI 接口、Swagger 文档和 Streamlit 中文聊天界面
- SQLite 自动建表与种子数据，Langfuse 可选接入

## 系统架构

![项目架构](images/architecture.png)

```text
用户
  ↓
Streamlit 中文界面
  ↓ HTTP
FastAPI /api/v1/chat
  ↓
LangGraph StateGraph
  ├─ triage：结合上下文识别 intent，并提取订单号、物流单号、邮箱
  ├─ tools：LLM 选择工具，工具调用 Service 访问 SQLite
  ├─ retry：仅在真实工具执行错误时最多重试 3 次
  └─ response：业务请求根据 Tool Results 回复；一般问题由 LLM 直接回答
  ↓
用户
```

内部 intent 和 Tool 函数名继续使用英文标识，确保 API、LangGraph 路由和第三方集成稳定；所有面向用户的界面、提示词、业务结果和 API 说明均已中文化。

## 快速开始

### 环境要求

- Python 3.11 或更高版本
- Git
- OpenAI API Key，或兼容 OpenAI Chat Completions / Tool Calling 的服务

### macOS / Linux

```bash
git clone https://github.com/muyang2715/ecommerce-ai-agent-cn.git
cd ecommerce-ai-agent-cn
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python run.py
```

### Windows PowerShell

```powershell
git clone https://github.com/muyang2715/ecommerce-ai-agent-cn.git
Set-Location ecommerce-ai-agent-cn
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

如果 PowerShell 禁止激活脚本，可仅对当前终端执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 环境变量

编辑 `.env`：

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-4o
TEMPERATURE=0.0

API_HOST=0.0.0.0
API_PORT=8000
```

`OPENAI_BASE_URL` 可留空以使用 OpenAI 官方服务。若使用兼容端点，请确认它完整支持 Tool Calling。不要把 `.env` 或真实密钥提交到 Git。

Langfuse 是可选功能；未提供 `LANGFUSE_PUBLIC_KEY` 和 `LANGFUSE_SECRET_KEY` 时会自动停用，不影响项目启动。

## 启动与访问

```bash
python run.py
```

- 中文聊天界面：[http://localhost:8501](http://localhost:8501)
- FastAPI Swagger：[http://localhost:8000/docs](http://localhost:8000/docs)
- 健康检查：[http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

`run.py` 会使用当前虚拟环境的 Python，同时启动 FastAPI 和 Streamlit。也可以分别运行：

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
streamlit run src/ui/streamlit_app.py --server.port 8501
```

若前后端不在同一台机器，可在启动 Streamlit 前设置 `CRATE_API_URL`：

```bash
export CRATE_API_URL="https://your-api.example.com/api/v1/chat"
```

## API

### 健康检查

```http
GET /api/v1/health
```

### 智能客服

```http
POST /api/v1/chat
Content-Type: application/json
```

请求：

```json
{
  "message": "查询订单 ORD-1002 的状态",
  "session_id": "可选会话标识"
}
```

响应包含中文 `response`、稳定的内部 `intent`、提取出的实体和真实 `tool_results`：

```json
{
  "response": "订单 ORD-1002 已发货……",
  "intent": "order_status",
  "order_id": "ORD-1002",
  "tracking_number": "",
  "customer_email": "",
  "tool_results": {
    "lookup_order": "📦 订单 #ORD-1002……"
  }
}
```

## LangGraph 工作流

```text
START
  ↓
triage
  ├─ general ───────────────→ response（LLM 开放式回答）
  └─ 需要业务数据 ─────────→ tools（含 product_discovery）
                              ├─ 成功/业务拒绝 → response
                              └─ 执行错误且重试<3 → tools
                                                   ↓
                                                response
                                                   ↓
                                                  END
```

`AgentState` 保存消息、intent、订单号、物流单号、客户邮箱、Tool Results、最终回复、重试次数和错误信息。LLM 在 `tools` 节点通过 LangChain 的函数调用协议选择工具；Tool 调用 Service，Service 使用参数化 SQL 访问 SQLite。有效的“未找到”或“不符合退货条件”属于业务结果，不会被误判为系统错误。

## Tools

| Tool | 用途 | 主要参数 | Service | 修改数据 |
|---|---|---|---|---|
| `lookup_order` | 按订单号查询详情 | `order_id` | `OrderService` | 否 |
| `lookup_orders_by_email` | 查询邮箱名下订单 | `email` | `OrderService` | 否 |
| `search_orders` | 按姓名、商品或部分订单号搜索 | `query` | `OrderService` | 否 |
| `search_product_catalog` | 商品搜索、预算筛选和导购 | `query`, `category`, `max_price` | `ProductService` | 否 |
| `track_shipment` | 查询物流状态和轨迹 | `tracking_number` | `ShippingService` | 否 |
| `get_return_policy` | 读取退货政策 | 无 | `ReturnsService` | 否 |
| `check_return_eligibility` | 判断订单能否退货 | `order_id` | `OrderService` | 否 |
| `initiate_return` | 创建退货申请和 RMA | `order_id`, `reason` | `ReturnsService` | 是 |

## SQLite

数据库会在首次启动或测试时自动创建于 `src/data/ecommerce.db`。

| 表 | 用途 | 初始数据 |
|---|---|---:|
| `orders` | 订单、客户、商品、状态、金额、地址 | 12 条 |
| `shipments` | 承运商、物流状态、预计送达与轨迹 | 9 条 |
| `returns` | RMA、原因、状态与退款金额 | 按需创建 |
| `products` | 商品名称、品类、价格、描述、关键词和库存 | 16 条 |

项目不会在中文化过程中改写原始英文姓名、商品名和地址；这些是业务数据，不是界面文案。

## 演示问题

| 中文输入 | 预期 Tool |
|---|---|
| `查询订单 ORD-1002 的状态` | `lookup_order` |
| `查询物流 FDX-78901234` | `track_shipment` |
| `请介绍一下退货政策` | `get_return_policy` |
| `我想退回 ORD-1001` | `check_return_eligibility` |
| `查询 james@example.com 的订单` | `lookup_orders_by_email` |
| `帮我找键盘订单` | `search_orders` |
| `150 美元以内推荐一款办公键盘` | `search_product_catalog` |
| `那再便宜一点的办公配件呢？` | 延续多轮上下文，再次调用 `search_product_catalog` |
| `介绍一下后端开发` | `general`，无需 Tool，由 LLM 直接回答 |
| `订单 ORD-1008 可以退货吗？` | `check_return_eligibility`，业务拒绝 |
| `追踪 UPS-99887766` | `track_shipment` |

Streamlit 回复下方的“查看处理详情与 Tool Results”会显示 intent、识别实体、实际调用工具和原始工具结果。

## 测试

```bash
pytest tests/ -v
```

测试覆盖 Order、Shipping、Returns、Product Service，8 个 Agent Tools 中的主要路径，以及 LangGraph 构建和条件路由。当前共 28 项，测试无需 LLM Key。

## 项目结构

```text
ecommerce-ai-agent-cn/
├── .streamlit/
│   └── config.toml              # 固定浅色主题，避免输入栏跟随系统变暗
├── run.py
├── requirements.txt
├── README.md
├── REPRODUCTION_NOTES.md
├── INTERVIEW_CHEATSHEET.md
├── src/
│   ├── agent/          # State、Tools、Nodes、Graph
│   ├── api/            # FastAPI 路由与 Schema
│   ├── services/       # SQLite 与业务服务
│   ├── observability/  # 可选 Langfuse
│   └── ui/             # Streamlit 中文 Claude 风格界面
└── tests/
```

## Vercel 部署提示

该项目当前是本地双进程架构，不能原样作为一个 Vercel 项目完整运行：

- `run.py` 同时启动 FastAPI 与 Streamlit 两个常驻服务，不符合单个 Vercel Function 的进程模型。
- Vercel Functions 的本地文件系统不能作为 SQLite 的持久共享存储。
- 当前多轮上下文保存在单进程内存中，Serverless 多实例之间不会共享。
- Streamlit 依赖使 Python 部署包较大，生产环境还需要认证、限流和严格 CORS。

本轮仅完成 GitHub 代码托管和本地可演示版本，没有假装完成 Vercel 云部署。完整风险清单见 [REPRODUCTION_NOTES.md](REPRODUCTION_NOTES.md)。若后续需要上线，建议拆分前端/API，并先把 SQLite 替换为托管数据库。

## 原项目与 License

- 原仓库：[m-peker/ecommerce-ai-agent](https://github.com/m-peker/ecommerce-ai-agent)
- 原作者：[@m-peker](https://github.com/m-peker)
- License：[MIT](LICENSE)

中文化版本保留原作者版权、README 来源说明和 Git 历史。
