# 面试讲解速记（2 分钟）

这个项目解决的是电商客服中订单、物流和退货问题的自动处理。用户不需要记命令，只要说“我的键盘订单在哪”或“ORD-1001 能退吗”，Agent 就能识别意图、提取实体、选择工具、查询业务数据并组织回复。

技术架构从前到后是 Streamlit、FastAPI、LangGraph、7 个 LangChain Tool、Service 层和 SQLite。Streamlit 负责聊天演示与 Details 展示；FastAPI 提供类型化的 `/health` 和 `/chat` 接口；SQLite 保存 12 个订单、9 个物流记录及运行时创建的退货 RMA。

它不是普通 ChatBot，因为模型不只是生成文字，还通过 Function Calling 决定是否以及如何执行真实业务函数。比如模糊的“keyboard order”会选择 `search_orders(query="keyboard")`，物流号会选择 `track_shipment`，退货请求会先做资格判断。

LangGraph 把流程显式建成三个节点：Triage 负责 intent 和实体提取，Tool Node 负责 LLM 选工具并执行，Response Node 根据 Tool Result 生成最终回复。条件边让 general 问题跳过工具，工具报错时最多执行 3 次工具尝试后再降级回复。

Tool 本身只是带 `@tool` 的 Python 函数，内部调用 Order、Shipping 或 Returns Service；Service 再用参数化 SQL 访问 SQLite。这样 LLM 不直接碰数据库，业务逻辑也能在没有 API Key 的情况下独立测试。

失败处理上，Tool 异常会写入 `tool_results`/`error_message`，Router 检测错误并重试，Response 最终有本地 fallback。要注意 upstream 当前把 `❌` 业务拒绝也当成错误重试，而且 triage 异常会静默降级成 general，这是后续应修复的可靠性问题。
