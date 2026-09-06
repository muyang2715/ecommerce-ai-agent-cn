# 项目简介

Crate 是一个电商客服 ReAct Agent。它用 OpenAI 模型完成意图识别、实体提取、工具选择和最终回复，用 LangGraph 显式组织流程，通过 7 个 LangChain Tool 访问 SQLite 中的订单、物流和退货服务，并由 FastAPI 暴露接口、Streamlit 提供演示 UI。

本次工作定位为开源项目复现：保留原作者 Git 历史、README、LICENSE 和业务逻辑，修复本地启动兼容性，并完成中文化与 Claude 风格 UI 优化。

# 原仓库地址

- <https://github.com/m-peker/ecommerce-ai-agent>
- 中文版本：<https://github.com/muyang2715/ecommerce-ai-agent-cn>
- 本次克隆提交：`3d38d5a`（`docs: add demo screenshots to README`）
- 本地目录：`/Users/xmyang/Documents/agent 项目/ecommerce-ai-agent-reproduction`

# 本地环境

实际验证环境不是 Windows，而是：

- macOS 15.2，Apple Silicon arm64
- Git 2.39.5
- 系统 `python3` 3.9.6（不符合项目 Python 3.11+ 要求，未用于项目）
- 项目解释器 Python 3.12.14
- 虚拟环境：`venv`
- 安装前端口 8000、8501 均未占用
- Vercel CLI 未安装；未创建或执行远程部署

关键实装版本：

| 包 | 版本 |
|---|---:|
| langgraph | 1.2.11 |
| langchain | 1.4.0 |
| langchain-openai | 1.6.0 |
| openai | 3.8.0 |
| fastapi | 0.141.1 |
| uvicorn | 0.52.4 |
| streamlit | 1.63.0 |
| pydantic | 2.13.5 |
| langfuse | 4.15.1 |
| pytest | 9.1.1 |

`requirements.txt` 只给出了最低版本，没有锁文件；因此未来重新安装可能得到不同版本。当前组合已经通过全部测试和服务启动验证。

# 安装步骤

Windows PowerShell 推荐步骤：

```powershell
git clone https://github.com/m-peker/ecommerce-ai-agent.git ecommerce-ai-agent-reproduction
Set-Location ecommerce-ai-agent-reproduction

# 先确认可用版本；如果没有 3.11+，应先安装合适版本，不要用 3.9 强装。
py -0p
py -3.11 -m venv venv

# 仅对当前 PowerShell 进程放宽脚本策略（若激活被策略阻止）
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
Copy-Item .env.example .env
```

Windows CMD 激活命令：

```bat
venv\Scripts\activate.bat
```

本次实际执行的 macOS 命令：

```bash
python3.12 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m pip check
```

# 环境变量

本地 `.env` 已创建并由 `.gitignore` 排除。当前使用用户提供的 OpenAI-compatible 端点；报告不保存或回显完整 Key：

```dotenv
OPENAI_API_KEY=<redacted-local-secret>
OPENAI_BASE_URL=https://apihub.agnes-ai.com/v1
OPENAI_MODEL=agnes-2.5-flash
TEMPERATURE=0.0
API_HOST=0.0.0.0
API_PORT=8000
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

注意：

- 不要提交 `.env`，不要在日志或截图中展示完整 Key。
- 当前本地 Key 已配置；它只存在于被 Git 忽略的 `.env`。
- 代理端点不提供 upstream 默认的 `gpt-4o`，调用时返回 `503 model_not_found`。从该端点的 `/models` 返回列表中选择了 `agnes-2.5-flash`；普通回复和 Function Calling 探针均通过。
- 代码和 `.env.example` 的 upstream 默认值是 `gpt-4o`；README 的架构说明又写了 `GPT-4o-mini`，这是 upstream 文档不一致。只有本地 `.env` 为兼容用户指定端点而改用 `agnes-2.5-flash`。
- Langfuse 是可选项。Key 为空时，`init_langfuse()` 记录 tracing disabled 并正常返回，不阻塞启动。

# 启动方式

激活虚拟环境后：

```powershell
python run.py
```

打开：

- FastAPI：<http://localhost:8000>
- Swagger：<http://localhost:8000/docs>
- Streamlit：<http://localhost:8501>

如果希望分别启动并保留两份日志：

```powershell
# PowerShell 窗口 1
.\venv\Scripts\Activate.ps1
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# PowerShell 窗口 2
.\venv\Scripts\Activate.ps1
python -m streamlit run src/ui/streamlit_app.py --server.port 8501 --server.headless true
```

本次验证结果：8000 和 8501 均真实监听；`/api/v1/health`、`/docs` 和 Streamlit 根页面均返回 HTTP 200。

# 测试结果

执行命令：

```powershell
python -m pytest tests/ -v
```

结果：

- 收集：24
- 通过：24
- 失败：0
- 跳过：0
- 实际耗时：2.07 秒
- `pip check`：`No broken requirements found.`
- `compileall`：通过

测试覆盖 Service、7 个 Tool 中的主要只读工具、退货 Service、Graph 构建和 triage 后条件路由。测试不调用 LLM，因此不需要 OpenAI Key。

# 系统架构

```text
用户
  ↓
Streamlit（HTTP POST）
  ↓
FastAPI /api/v1/chat
  ↓
LangGraph StateGraph
  ↓
Triage Node（LLM：intent + entities）
  ↓ 条件边
Tool Node（LLM Function Calling + Tool 执行）
  ↓
Order / Shipping / Returns Service
  ↓
SQLite
  ↓
Tool Results 写回 AgentState
  ↓ 成功或最多 3 次工具尝试
Response Node（LLM 或本地 fallback）
  ↓
FastAPI ChatResponse → Streamlit → 用户
```

## AgentState 保存什么

`src/agent/state.py` 定义了共享 `TypedDict`：

- `messages`：LangChain 消息列表，使用 `add_messages` reducer，追加式合并。
- `intent`：`order_status`、`shipping_tracking`、`return_request`、`return_policy` 或 `general`。
- `order_id`、`tracking_number`、`customer_email`：triage 提取出的实体。
- `tool_results`：Tool 名称到字符串结果的字典。
- `final_response`：最终用户回复。
- `retry_count`、`error_message`：工具重试和错误处理状态。

当前实现没有把 Tool 的 `AIMessage`/`ToolMessage` 追加回 `messages`；工具观察结果只进入 `tool_results`。

## FastAPI 与 Streamlit 如何连接

- `src/api/routes.py` 为每次请求构造初始 `AgentState`，同步调用 `agent_graph.invoke()`，再把 state 中的 intent、实体、tool results 和 final response 映射为 `ChatResponse`。
- `src/ui/streamlit_app.py` 向 `CRATE_API_URL` 指定的地址发送请求，未设置时使用 `http://localhost:8000/api/v1/chat`。
- UI 的“查看处理详情与 Tool Results”根据返回的 intent、实体和 `tool_results` 展示可核验执行记录；它不是模型的隐藏思维链。
- 浏览器实测确认首页、4 个中文快捷操作、聊天输入和详情展开区可用。真实点击“查询 ORD-1002”后，详情展示 `order_status`、`ORD-1002`、`lookup_order` 和完整中文工具结果。

# LangGraph 工作流

真实 `StateGraph`：

```text
START
  ↓
triage
  ├─ intent == general ─────────────→ response ─→ END
  └─ 其他 intent ─→ tools
                       ├─ Tool 执行异常，且 retry_count < 3
                       │       └────────────────→ tools（Retry）
                       └─ 成功或 retry_count >= 3 ─→ response ─→ END
```

一次正常业务请求计划经过：

```text
Triage → 条件 Router → Tool Execution → after_tools Router → Response
```

具体机制：

1. Triage LLM 只返回 JSON；节点解析 intent、订单号、物流号和邮箱。
2. `should_use_tools()` 仅对 `general` 跳过工具，其他 intent 全部进入 Tool Node。
3. Tool Node 用 `ChatOpenAI(...).bind_tools(ALL_TOOLS)` 把 7 个函数 schema 交给模型，由模型决定调用哪个工具及参数。
4. 节点按工具名在 `ALL_TOOLS` 中查找并执行 `tool.invoke(tool_args)`。
5. Tool 调用对应 Service；Service 每次通过 `get_connection()` 打开 SQLite，查询/写入后关闭连接。
6. 结果写入 `tool_results`，`retry_count` 每次 Tool Node 执行加 1。
7. `after_tools()` 判断错误并决定重试或进入 Response。
8. Response Node 用 LLM 把原始工具结果组织成简体中文；LLM 失败时直接拼接原始结果。

重试的真实边界：

- 第 1、2 次工具结果被判断为错误时会重试。
- 第 3 次仍错误则进入 Response，不再继续。
- upstream 原实现把所有 `❌` 结果都视为系统错误；本轮已最小修复为只重试 `error`、“调用工具失败”和“未找到工具”。订单不存在或超过退货期等有效业务结果直接进入 Response。
- triage 的所有异常被捕获后直接降级为 `general`，不会触发 Tool Retry。
- LLM 没有返回任何 `tool_calls` 时，空 `tool_results` 被当作成功进入 Response。

# Tools 列表

| Tool | 用途 | 输入参数 | 调用的 Service | 修改数据 | 典型触发语句 |
|---|---|---|---|---|---|
| `lookup_order` | 按订单号查询详情 | `order_id: str` | `OrderService.get_order` | 否 | `查询订单 ORD-1002 的状态` |
| `lookup_orders_by_email` | 查询邮箱关联的全部订单 | `email: str` | `OrderService.get_orders_by_email` | 否 | `查询 james@example.com 的订单` |
| `search_orders` | 按订单号、客户名或商品名模糊搜索 | `query: str` | `OrderService.search_orders` | 否 | `帮我找键盘订单` |
| `track_shipment` | 查询承运商、状态和物流事件 | `tracking_number: str` | `ShippingService.track` | 否 | `追踪 UPS-99887766` |
| `get_return_policy` | 返回退货与退款政策 | 无 | `ReturnsService.get_policy` | 否 | `请介绍退货政策` |
| `check_return_eligibility` | 判断订单是否已送达且在 14 天内 | `order_id: str` | `OrderService.can_return` | 否 | `ORD-1001 可以退货吗？` |
| `initiate_return` | 再次检查资格并创建 RMA | `order_id: str`, `reason: str` | `OrderService` + `ReturnsService.create_return` | 是，写 `returns` | `ORD-1001 有缺陷，我要退货` |

# SQLite 数据结构

数据库路径：

```text
/Users/xmyang/Documents/agent 项目/ecommerce-ai-agent-reproduction/src/data/ecommerce.db
```

注意 README 的目录树写的是根目录 `data/`，真实代码 `DB_PATH` 位于 `src/data/ecommerce.db`。

## `orders`

字段：`order_id`（PK）、`customer_name`、`email`、`items`（JSON）、`status`、`total`、`created_at`、`shipping_address`、`tracking_number`。

初始化 12 行。示例：

| order_id | customer | email | status | total | tracking |
|---|---|---|---|---:|---|
| ORD-1001 | James Wilson | james@example.com | delivered | 105.97 | FDX-78901234 |
| ORD-1002 | Sarah Chen | sarah@example.com | shipped | 149.99 | UPS-45678901 |
| ORD-1003 | Marcus Rivera | marcus@example.com | confirmed | 499.99 | 空 |

## `shipments`

字段：`tracking_number`（PK）、`carrier`、`status`、`estimated_delivery`、`events`（JSON）。初始化 9 行。

示例：

| tracking_number | carrier | status |
|---|---|---|
| FDX-78901234 | FedEx | delivered |
| UPS-45678901 | UPS | in_transit |
| UPS-99887766 | UPS | out_for_delivery |

## `returns`

字段：`rma_number`（PK）、`order_id`（FK）、`reason`、`status`、`refund_amount`、`created_at`。

初始 seed 为 0 行；本轮验证后为 4 行：三次完整 pytest 创建 `RMA-1000`、`RMA-1002`、`RMA-1003`，显式 `initiate_return` 工具演示创建 `RMA-1001`。这些行都是项目自身功能产生的测试数据，没有改写订单或物流 seed。

# API 接口

## `GET /api/v1/health`

实际返回 HTTP 200：

```json
{"status":"ok","version":"1.0.0"}
```

这是浅健康检查，不验证 SQLite 或 OpenAI 可用性。

## `POST /api/v1/chat`

请求：

```json
{
  "message": "What's the status of order ORD-1002?",
  "session_id": "default"
}
```

响应字段：`response`、`intent`、`order_id`、`tracking_number`、`customer_email`、`tool_results`。

`session_id` 当前只被 schema 接收，未用于记忆、checkpoint 或隔离会话。

缺少 Key、模型不存在或 triage 遇到 429 时，此请求仍返回 HTTP 200，但实际响应会错误地降级为 `intent=general`、空实体和空 `tool_results`。这是 upstream 的静默异常行为。

# 演示 Case

所有 8 条都先通过了无需 LLM 的真实 Tool + SQLite 直接验证，随后也全部通过真实 `/chat` 端到端验证。批量首轮在第 7 条遇到第三方免费额度 429，第 8 条因此在 triage 降级；等待限流窗口恢复并修复无效业务重试后，两条均补测成功。

| 用户输入 | 实际/预期 intent | 实际或直接验证的 Tool 与参数 | Tool 结果摘要 | 端到端状态 |
|---|---|---|---|---|
| 查询订单 ORD-1002 的状态 | order_status | `lookup_order(order_id="ORD-1002")` | Sarah Chen，已发货，$149.99，UPS-45678901 | HTTP 200，成功 |
| 查询物流 FDX-78901234 | shipping_tracking | `track_shipment(tracking_number="FDX-78901234")` | FedEx，已送达，4 条事件 | HTTP 200，成功 |
| 请介绍一下退货政策 | return_policy | `get_return_policy()` | 14 天、3～5 个工作日退款等 | HTTP 200，成功 |
| 我想退回 ORD-1001 | return_request | `check_return_eligibility(order_id="ORD-1001")` + `get_return_policy()` | 符合条件 + 政策 | HTTP 200，成功 |
| 查询 james@example.com 的订单 | order_status | `lookup_orders_by_email(email="james@example.com")` | ORD-1011、ORD-1001 | HTTP 200，成功 |
| 帮我找键盘订单 | order_status | `search_orders(query="keyboard")` | 找到 ORD-1002 Mechanical Keyboard | HTTP 200，成功 |
| 订单 ORD-1008 可以退货吗？ | return_request | `check_return_eligibility(order_id="ORD-1008")` | 14 天窗口已过期 | HTTP 200，成功（业务拒绝） |
| 追踪 UPS-99887766 | shipping_tracking | `track_shipment(tracking_number="UPS-99887766")` | UPS，派送中 | HTTP 200，成功 |

`initiate_return(order_id="ORD-1001", reason="defective")` 也已真实执行，成功创建 `RMA-1001`、退款金额 105.97。

端到端 LLM 状态：8/8 的真实 intent、Tool Calling、SQLite Tool Results 和最终自然语言回复均已验证成功。

# 中文化与 UI 优化

1. Triage、Tool Calling 上下文和 Response Prompt 均支持中文输入，并强制使用简体中文回复；内部 intent 保持英文枚举。
2. 7 个 Tool 的描述、状态、错误和结果全部中文化；英文商品、姓名与地址作为原始业务数据保留。
3. FastAPI 标题、Schema 描述、启动日志与错误提示已中文化。
4. Streamlit 改为 Claude 风格的暖米色画布、纸张卡片、陶土橙点缀和克制留白。
5. 字体栈优先使用 macOS 的 `STFangsong`/`华文仿宋`，并提供 Windows `FangSong`/`FangSong_GB2312` 与 CJK Serif 回退。
6. 详情区显示 intent、识别实体、Tool 名和真实 Tool Results，不展示或伪造隐藏思维链。
7. 已用自动化浏览器检查桌面布局、快捷操作、中文回复和详情展开：页面非空、无错误遮罩、无捕获到的控制台错误。

# 本地兼容性修改

兼容性修改保持最小范围，没有改订单、物流或退货的核心业务规则：

1. upstream 把 Python 固定为 `venv/Scripts/python.exe`，导致 macOS/Linux 不能运行；改为 `sys.executable`。在 Windows 从已激活的 `venv` 执行时仍然得到 `venv\Scripts\python.exe`。
2. Streamlit 增加 `--server.headless true`，避免无图形/自动化环境启动挂起。
3. 移除 Streamlit 的 stdout/stderr 丢弃，使启动失败能看到真实日志。
4. 增加 `OPENAI_BASE_URL` 配置并传给 `ChatOpenAI`，支持用户指定的 OpenAI-compatible 端点。
5. 兼容模型偶发把 Response 输出成 `<tool_call>` 标记；仅在已有真实 Tool Results 且检测到该标记时，使用确定性中文 formatter。
6. 修正 upstream Retry 判定：有效的“未找到”或“不符合条件”业务结果不再重试，只有执行异常才重试。
7. `.gitignore` 增加 SQLite WAL/SHM sidecar，避免运行中的 `*.db-wal`、`*.db-shm` 被误提交。

生成但被 Git 忽略的本地文件：`.env`、`venv/`、`src/data/ecommerce.db`。

# Vercel 部署风险审计

结论：当前仓库适合本地双进程演示，但不能原样完整部署到 Vercel。没有执行远程部署，也没有更换数据库或重构 UI。

| 严重度 | 风险 | 证据与影响 | 最小后续方向（非本轮改动） |
|---|---|---|---|
| 阻塞 | SQLite 无法作为 Vercel Functions 的持久数据库 | `init_db()` 在 startup 写 `src/data/ecommerce.db`；Vercel 官方明确说明 Functions 存储是 ephemeral，SQLite 不能用于永久/并发共享写入 | 部署前换成托管数据库；本地仍保留 SQLite |
| 阻塞 | Streamlit 不会随 FastAPI 自动成为同一部署的第二个常驻服务 | Vercel 能识别 `src/main.py` 中的 FastAPI `app`，但不会执行 `run.py` 同时监听 8000/8501 | API 和 UI 拆分部署，或把演示 UI 放到支持 Streamlit 常驻进程的平台 |
| 已缓解 | UI API 地址原先硬编码 localhost | 已新增 `CRATE_API_URL`；云端仍需配置公开 API 地址并设置严格 CORS | 部署时设置环境变量和真实 UI origin |
| 高 | Python Function 包体接近限制 | 本机 `site-packages` 已约 455 MB；Streamlit 带入 PyArrow/Pandas/NumPy，Vercel 标准 Python bundle 上限 500 MB，且 Python 不 tree-shake | 拆分 API/UI requirements，排除 tests/images，增加锁文件 |
| 高 | 公开 `/chat` 无认证、速率限制或用量保护 | 任何访问者都能消耗 OpenAI 配额 | 上线前加认证、限流和预算告警 |
| 高 | 本地 RMA 编号生成不适合横向并发 | `SELECT 最大 RMA + 1` 再 INSERT；多实例可竞争并产生主键冲突 | 外部数据库序列/事务/唯一重试 |
| 中 | 依赖版本不可复现 | 所有核心包只有 `>=`；本轮已解析到 LangGraph 1.2、LangChain 1.4、Langfuse 4.15 | 验证 Windows 后锁定已知可用版本 |
| 中 | `/chat` 是 async route，但内部同步执行 3 次 LLM/图调用 | 阻塞事件循环；冷启动和外部 API 延迟会增加函数时长 | 使用 LangGraph async API 或把同步调用放入线程 |
| 中 | CORS 允许 `*` 且 `allow_credentials=True` | 生产权限边界过宽且配置组合不合理 | 限定真实 UI origin；无必要时关闭 credentials |
| 已缓解 | upstream Tool Retry 把业务拒绝当系统错误 | 原代码会对 `❌ not found/expired` 重试；本地复现已将其收窄为只重试执行异常 | 若部署 upstream 原提交，需带上本轮最小修复 |
| 中 | 缺 Key/triage 异常返回 200 general | 监控看似正常，业务实际失败 | 启动时校验 Key，或 API 返回明确 503/错误码 |
| 低 | 健康检查过浅 | `/health` 永远返回 ok，不检查 DB/模型 | 增加 readiness 检查 |

Vercel 当前官方资料：

- [FastAPI 入口和部署方式](https://vercel.com/docs/frameworks/backend/fastapi)
- [Python Runtime、版本和 500 MB 标准包体限制](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Functions 时长、内存和包体限制](https://vercel.com/docs/functions/limitations)
- [Vercel 官方：SQLite 不适用于 Functions 的持久存储](https://vercel.com/kb/guide/is-sqlite-supported-in-vercel)

# 当前已知问题

1. 用户指定的第三方端点对免费用户曾返回 429；限流恢复后 8/8 场景均成功，但连续演示仍可能再次触发免费额度限制。
2. 当前实测平台为 macOS，不应声称 Windows 已实际运行；上面的 PowerShell 命令按 Windows 目标整理。
3. `triage_node` 吞掉所有异常并返回 `general`，使缺 Key、模型不存在和限流看起来像普通问候。
4. 本轮已区分业务失败和系统失败，但系统错误重试仍没有指数退避；429 会立即重试，可能加速耗尽额度。
5. LLM 没有选择工具时不会重试。
6. `session_id` 未实现会话记忆。
7. 退货 14 天判断使用订单创建时间，不是单独的送达时间。
8. 同一订单可以创建多个 RMA；本轮测试已经展示这一点。
9. 用户把 API Key 直接发送到了聊天中；演示后应在提供商控制台轮换该 Key。

# 成功标准状态

- [x] 项目成功克隆
- [x] 虚拟环境创建成功
- [x] requirements 安装成功
- [x] SQLite 数据正常
- [x] pytest 能运行（24/24）
- [x] FastAPI 正常启动
- [x] `/docs` 可以访问
- [x] `/health` 正常
- [x] `/chat` HTTP/Schema 正常，8/8 真实 LLM 业务请求成功
- [x] Streamlit 正常启动
- [x] 订单查询 Tool/Service 成功
- [x] 物流查询 Tool/Service 成功
- [x] 退货政策 Tool/Service 成功
- [x] 退货资格判断 Tool/Service 成功
- [x] 真实 OpenAI-compatible Tool Calling 已验证
- [x] LangGraph 构建和路由逻辑测试通过
- [x] 中文 Claude 风格 UI 与真实 Tool Results 展开验证成功
- [x] `REPRODUCTION_NOTES.md` 已生成

# 后续可以扩展的方向

本地复现完成后，再考虑：

1. 在 Windows 3.11/3.12 上重跑安装、24 个测试和两个服务。
2. 为第三方端点配置足够额度或请求节流，避免连续演示触发 429。
3. 锁定依赖版本，建立可重复安装基线。
4. 若决定上 Vercel，先拆分 UI/API 并替换 SQLite；不要在当前复现阶段直接大改。
5. 为 Tool Retry 增加结构化错误类型，并为 `/chat` 增加失败可观测性、认证和限流。
