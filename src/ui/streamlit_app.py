"""Crate 中文智能客服界面。"""

import html
import os

import requests
import streamlit as st


st.set_page_config(
    page_title="Crate 智能客服",
    page_icon="◉",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --canvas: #f7f4ef;
        --paper: #fffdfa;
        --ink: #2d2926;
        --muted: #746d65;
        --line: #e6dfd6;
        --accent: #c96442;
        --accent-soft: #f5e8e0;
        --sage: #61766a;
        --font-cn: "Crate FangSong", "STFangsong", "FangSong",
                   "FangSong_GB2312",
                   "华文仿宋", "Noto Serif CJK SC", serif;
    }

    @font-face {
        font-family: "Crate FangSong";
        src: local("STFangsong"), local("FangSong"),
             local("FangSong_GB2312"), local("华文仿宋");
        font-display: swap;
    }

    html, body, .stApp,
    .stApp *:not([data-testid="stIconMaterial"]) {
        font-family: var(--font-cn) !important;
    }
    [data-testid="stIconMaterial"] {
        font-family: "Material Symbols Rounded" !important;
    }
    .stApp {
        color: var(--ink);
        background:
            radial-gradient(circle at 12% 0%, rgba(201, 100, 66, .08), transparent 25rem),
            var(--canvas);
    }
    .main .block-container {
        max-width: 860px;
        padding: 2.2rem 1.5rem 7rem;
    }
    #MainMenu, footer, header [data-testid="stDecoration"],
    [data-testid="stToolbar"], .stDeployButton { display: none !important; }

    .hero {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.5rem;
        padding: 1.2rem 1.35rem;
        margin-bottom: 1rem;
        border: 1px solid var(--line);
        border-radius: 22px;
        background: rgba(255, 253, 250, .88);
        box-shadow: 0 12px 35px rgba(72, 55, 41, .06);
        backdrop-filter: blur(12px);
    }
    .brand { display: flex; align-items: center; gap: .8rem; }
    .brand-mark {
        display: grid;
        width: 42px;
        height: 42px;
        place-items: center;
        border-radius: 14px;
        color: #fffaf5;
        background: var(--accent);
        box-shadow: 0 7px 18px rgba(201, 100, 66, .22);
        font-size: 1.2rem;
    }
    .brand-name {
        color: var(--ink);
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: .04em;
    }
    .brand-sub { margin-top: .13rem; color: var(--muted); font-size: .83rem; }
    .online {
        display: flex;
        align-items: center;
        gap: .42rem;
        color: var(--sage);
        font-size: .8rem;
        white-space: nowrap;
    }
    .online::before {
        width: .48rem;
        height: .48rem;
        border-radius: 50%;
        background: #6f927d;
        content: "";
        box-shadow: 0 0 0 4px rgba(111, 146, 125, .12);
    }
    .intro { padding: .25rem .2rem .75rem; }
    .intro-title { margin: 0; color: var(--ink); font-size: 1.52rem; font-weight: 700; }
    .intro-copy { margin-top: .35rem; color: var(--muted); font-size: .94rem; line-height: 1.7; }

    [data-testid="stButton"] > button {
        min-height: 2.7rem;
        border: 1px solid var(--line);
        border-radius: 13px;
        color: #534b45;
        background: rgba(255, 253, 250, .9);
        font-size: .83rem;
        transition: transform .15s ease, border-color .15s ease, background .15s ease;
        box-shadow: none;
    }
    [data-testid="stButton"] > button:hover {
        border-color: #d5a28e;
        color: #9b4d34;
        background: var(--accent-soft);
        transform: translateY(-1px);
    }
    hr { margin: 1rem 0 1.15rem !important; border-color: var(--line) !important; }

    [data-testid="stChatMessage"] {
        margin: .72rem 0;
        padding: 1rem 1.1rem;
        border: 1px solid var(--line);
        border-radius: 18px;
        background: var(--paper);
        box-shadow: 0 5px 18px rgba(72, 55, 41, .035);
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        margin-left: 8%;
        border-color: #ead4c8;
        background: #faf0e9;
    }
    [data-testid="stChatMessageAvatar"] {
        width: 2rem;
        height: 2rem;
        color: var(--accent);
        background: transparent;
    }
    [data-testid="stChatMessageContent"] { color: var(--ink); line-height: 1.72; }

    [data-testid="stExpander"] {
        margin-bottom: .65rem;
        border: 1px solid var(--line);
        border-radius: 12px;
        background: #fbf8f3;
    }
    [data-testid="stExpander"] summary { color: var(--muted); font-size: .83rem; }
    .trace-line { margin: .32rem 0; color: #615950; font-size: .82rem; line-height: 1.6; }
    .trace-tool {
        margin: .45rem 0 .65rem;
        padding: .65rem .75rem;
        border-left: 3px solid #d9a38e;
        border-radius: 0 8px 8px 0;
        color: #625a53;
        background: #fffdfa;
        font-size: .78rem;
        white-space: pre-wrap;
    }

    [data-testid="stBottom"],
    [data-testid="stBottom"] > div {
        background: linear-gradient(
            to bottom,
            rgba(247, 244, 239, 0),
            var(--canvas) 34%,
            var(--canvas) 100%
        ) !important;
    }
    [data-testid="stBottomBlockContainer"] {
        background: transparent !important;
    }
    [data-testid="stChatInput"] {
        border: 1px solid #dcd2c8;
        border-radius: 17px;
        background: var(--paper) !important;
        box-shadow: 0 12px 35px rgba(72, 55, 41, .1);
    }
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] textarea {
        background: var(--paper) !important;
    }
    [data-testid="stChatInput"] textarea {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        caret-color: var(--accent) !important;
        opacity: 1 !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #81786f !important;
        -webkit-text-fill-color: #81786f !important;
        opacity: 1 !important;
    }
    [data-testid="stChatInput"] button {
        color: var(--accent) !important;
        background: #f4e8e1 !important;
    }
    [data-testid="stChatInput"] button svg {
        color: var(--accent) !important;
        fill: var(--accent) !important;
    }
    [data-testid="stSpinner"] { color: var(--muted); }

    @media (max-width: 640px) {
        .main .block-container { padding: 1rem .7rem 6rem; }
        .hero { padding: 1rem; border-radius: 17px; }
        .online { display: none; }
        .intro-title { font-size: 1.3rem; }
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
        [data-testid="column"] { min-width: 46% !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="brand">
        <div class="brand-mark">C</div>
        <div>
          <div class="brand-name">Crate 智能客服</div>
          <div class="brand-sub">订单 · 物流 · 退货，一站式智能协助</div>
        </div>
      </div>
      <div class="online">服务在线</div>
    </div>
    <div class="intro">
      <p class="intro-title">今天想查询什么？</p>
      <div class="intro-copy">我可以读取真实订单与物流数据，也能判断退货资格。请选择快捷问题，或直接输入你的需求。</div>
    </div>
    """,
    unsafe_allow_html=True,
)

API_URL = os.getenv("CRATE_API_URL", "http://localhost:8000/api/v1/chat")

if "msgs" not in st.session_state:
    st.session_state.msgs = [
        {
            "role": "a",
            "text": "你好，我是 Crate 智能客服。你可以告诉我订单号、物流单号或注册邮箱，我会帮你查询。",
            "steps": None,
        }
    ]
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

INTENT_LABELS = {
    "order_status": "识别为订单查询",
    "shipping_tracking": "识别为物流追踪",
    "return_request": "识别为退货请求",
    "return_policy": "识别为退货政策咨询",
    "general": "识别为一般咨询",
}

TOOL_LABELS = {
    "lookup_order": "按订单号查询订单",
    "lookup_orders_by_email": "按邮箱查询全部订单",
    "search_orders": "模糊搜索订单与商品",
    "track_shipment": "查询承运商物流轨迹",
    "get_return_policy": "读取退货政策",
    "check_return_eligibility": "检查退货资格",
    "initiate_return": "创建退货申请",
}


def render_details(steps: dict | None) -> None:
    """展示可核验的路由和工具结果，不展示模型的隐藏思维过程。"""
    if not steps:
        return

    intent = steps.get("intent", "general")
    facts = []
    if steps.get("order_id"):
        facts.append(f"订单号：{steps['order_id']}")
    if steps.get("tracking_number"):
        facts.append(f"物流单号：{steps['tracking_number']}")
    if steps.get("customer_email"):
        facts.append(f"邮箱：{steps['customer_email']}")

    with st.expander("查看处理详情与 Tool Results", expanded=False):
        st.markdown(
            f'<div class="trace-line">● {html.escape(INTENT_LABELS.get(intent, "已分析请求"))}</div>',
            unsafe_allow_html=True,
        )
        if facts:
            st.markdown(
                f'<div class="trace-line">识别信息：{html.escape(" · ".join(facts))}</div>',
                unsafe_allow_html=True,
            )
        tools = steps.get("tool_results") or {}
        if not tools:
            st.markdown('<div class="trace-line">本次无需调用业务工具。</div>', unsafe_allow_html=True)
        for tool_name, result in tools.items():
            tool_title = TOOL_LABELS.get(tool_name, tool_name)
            st.markdown(
                f'<div class="trace-line">● Tool：{html.escape(tool_title)} '
                f'<code>{html.escape(tool_name)}</code></div>'
                f'<div class="trace-tool">{html.escape(str(result))}</div>',
                unsafe_allow_html=True,
            )


def call_api(query: str) -> tuple[str, dict | None]:
    """调用 FastAPI，并把错误转换成面向用户的中文提示。"""
    try:
        response = requests.post(API_URL, json={"message": query}, timeout=90)
        if response.status_code == 200:
            data = response.json()
            reply = data.get("response") or "抱歉，我暂时无法生成回复，请稍后重试。"
            steps = {
                key: data.get(key, "")
                for key in ["intent", "order_id", "tracking_number", "customer_email"]
            }
            steps["tool_results"] = data.get("tool_results", {})
            return reply, steps
        return f"服务请求失败（HTTP {response.status_code}），请稍后重试。", None
    except requests.exceptions.ConnectionError:
        return "**无法连接后端服务。** 请先在项目目录运行 `python run.py`。", None
    except requests.exceptions.Timeout:
        return "本次请求超时，请稍后再试。", None
    except Exception as exc:
        return f"请求发生错误：{exc}", None


QUICK_ACTIONS = [
    ("查询 ORD-1002", "查询订单 ORD-1002 的状态"),
    ("追踪 FDX-78901234", "查询物流 FDX-78901234"),
    ("了解退货政策", "请介绍一下退货政策"),
    ("查询我的订单", "查询 james@example.com 的订单"),
]

columns = st.columns(4)
for index, (label, query) in enumerate(QUICK_ACTIONS):
    with columns[index]:
        if st.button(label, use_container_width=True, key=f"quick_action_{index}"):
            st.session_state.pending_query = query
            st.rerun()

st.divider()

for message in st.session_state.msgs:
    role = "assistant" if message["role"] == "a" else "user"
    with st.chat_message(role):
        if role == "assistant":
            render_details(message.get("steps"))
        st.markdown(message["text"])


def render_exchange(query: str) -> None:
    """渲染并保存一轮对话。"""
    st.session_state.msgs.append({"role": "u", "text": query, "steps": None})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("正在理解问题并查询业务数据…"):
            reply, steps = call_api(query)
        render_details(steps)
        st.markdown(reply)
    st.session_state.msgs.append({"role": "a", "text": reply, "steps": steps})


if st.session_state.pending_query:
    pending_query = st.session_state.pending_query
    st.session_state.pending_query = None
    render_exchange(pending_query)
    st.rerun()

if prompt := st.chat_input("请输入订单号、物流单号或退货问题…"):
    render_exchange(prompt)
