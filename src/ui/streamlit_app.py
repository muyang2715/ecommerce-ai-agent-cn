"""Crate 中文智能客服界面。"""

import html
import os
import uuid

import requests
import streamlit as st


st.set_page_config(
    page_title="Crate 品牌智能助手",
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
        --paper-warm: #fbf6ef;
        --ink: #2d2926;
        --ink-soft: #554d46;
        --muted: #746d65;
        --line: #e6dfd6;
        --line-strong: #d6cabe;
        --accent: #c96442;
        --accent-ink: #914128;
        --accent-soft: #f5e8e0;
        --sage: #61766a;
        --focus: rgba(201, 100, 66, .28);
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
        background: var(--canvas);
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 900px;
        padding: 2rem 1.5rem 7.5rem;
    }
    #MainMenu, footer, header [data-testid="stDecoration"],
    [data-testid="stToolbar"], .stDeployButton { display: none !important; }

    .service-masthead {
        position: relative;
        overflow: hidden;
        padding: 1.05rem 1.2rem 0;
        margin-bottom: 1.35rem;
        border: 1px solid var(--line-strong);
        border-right: 6px solid var(--sage);
        border-radius: 7px 22px 7px 22px;
        background: var(--paper);
        box-shadow: 0 16px 42px rgba(72, 55, 41, .075);
    }
    .masthead-meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: .8rem;
        color: var(--muted);
        font-size: .68rem;
        letter-spacing: .16em;
        text-transform: uppercase;
    }
    .brand { display: flex; align-items: center; gap: .9rem; padding-bottom: 1rem; }
    .brand-mark {
        display: grid;
        width: 46px;
        height: 46px;
        place-items: center;
        border-radius: 50% 50% 48% 12px;
        color: #fffaf5;
        background: var(--accent);
        box-shadow: 0 7px 18px rgba(201, 100, 66, .22);
        font-size: 1.15rem;
        transform: rotate(-3deg);
    }
    .brand-mark span { transform: rotate(3deg); }
    .brand-name {
        color: var(--ink);
        font-size: 1.38rem;
        font-weight: 700;
        letter-spacing: .06em;
    }
    .brand-sub { margin-top: .18rem; color: var(--muted); font-size: .82rem; letter-spacing: .03em; }
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
    .service-route {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        margin: 0 -1.2rem;
        border-top: 1px dashed var(--line-strong);
        background: var(--paper-warm);
    }
    .route-stop {
        position: relative;
        padding: .7rem .85rem .72rem;
        color: var(--ink-soft);
        font-size: .73rem;
        letter-spacing: .04em;
    }
    .route-stop + .route-stop { border-left: 1px solid var(--line); }
    .route-stop b { margin-right: .38rem; color: var(--accent-ink); font-size: .66rem; font-weight: 400; }
    .intro { display: grid; grid-template-columns: 9rem 1fr; gap: 1.25rem; padding: .1rem .2rem .9rem; }
    .intro-kicker {
        padding-top: .38rem;
        color: var(--accent-ink);
        font-size: .67rem;
        letter-spacing: .18em;
        text-transform: uppercase;
    }
    .intro-title { margin: 0; color: var(--ink); font-size: 1.62rem; font-weight: 700; letter-spacing: .04em; }
    .intro-copy { max-width: 38rem; margin-top: .38rem; color: var(--muted); font-size: .9rem; line-height: 1.78; }
    .quick-label {
        margin: .1rem 0 .48rem;
        color: var(--muted);
        font-size: .69rem;
        letter-spacing: .14em;
    }

    [data-testid="stButton"] > button {
        min-height: 3rem;
        justify-content: flex-start;
        padding: .6rem .82rem;
        border: 1px solid var(--line);
        border-radius: 5px 13px 5px 13px;
        color: #534b45;
        background: var(--paper);
        font-size: .79rem;
        letter-spacing: .025em;
        transition: transform .16s ease, border-color .16s ease, background .16s ease;
        box-shadow: none;
    }
    [data-testid="stButton"] > button p {
        width: 100%;
        overflow: visible;
        text-align: left;
        text-overflow: clip;
        white-space: normal;
    }
    [data-testid="stButton"] > button:hover {
        border-color: #d5a28e;
        color: #9b4d34;
        background: var(--accent-soft);
        transform: translateY(-2px);
    }
    [data-testid="stButton"] > button:focus-visible,
    [data-testid="stChatInput"] textarea:focus-visible {
        outline: 3px solid var(--focus) !important;
        outline-offset: 2px;
    }
    hr { margin: 1.15rem 0 1.2rem !important; border-color: var(--line) !important; }

    [data-testid="stChatMessage"] {
        position: relative;
        margin: .82rem 0;
        padding: 1.05rem 1.15rem;
        border: 1px solid var(--line);
        border-left: 3px solid #d49a83;
        border-radius: 4px 17px 17px 17px;
        background: var(--paper);
        box-shadow: 0 8px 25px rgba(72, 55, 41, .045);
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        margin-left: 16%;
        border: 1px solid #ead4c8;
        border-right: 3px solid var(--accent);
        border-radius: 17px 4px 17px 17px;
        background: #f8ece4;
        box-shadow: none;
    }
    [data-testid="stChatMessageAvatar"] {
        width: 2rem;
        height: 2rem;
        color: var(--accent);
        background: transparent;
    }
    [data-testid="stChatMessageContent"] { color: var(--ink); font-size: .96rem; line-height: 1.76; }
    [data-testid="stChatMessageContent"] p:first-child { margin-top: 0; }
    [data-testid="stChatMessageContent"] p:last-child { margin-bottom: 0; }

    [data-testid="stExpander"] {
        margin-bottom: .72rem;
        border: 0;
        border-top: 1px dashed var(--line-strong);
        border-bottom: 1px dashed var(--line-strong);
        border-radius: 0;
        background: transparent;
    }
    [data-testid="stExpander"] summary { min-height: 2.35rem; color: var(--muted); font-size: .76rem; }
    .trace-line { margin: .32rem 0; color: #615950; font-size: .82rem; line-height: 1.6; }
    .trace-tool {
        margin: .45rem 0 .65rem;
        padding: .65rem .75rem;
        border-left: 2px solid #d9a38e;
        border-radius: 0 5px 5px 0;
        color: #625a53;
        background: var(--paper-warm);
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
        border-radius: 5px 17px 5px 17px;
        background: var(--paper) !important;
        box-shadow: 0 14px 38px rgba(72, 55, 41, .12);
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

    .service-masthead,
    .intro,
    [data-testid="stHorizontalBlock"],
    [data-testid="stChatMessage"] {
        animation: settle-in .42s ease both;
    }
    .intro { animation-delay: .05s; }
    [data-testid="stHorizontalBlock"] { animation-delay: .1s; }
    @keyframes settle-in {
        from { opacity: 0; transform: translateY(7px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 640px) {
        [data-testid="stMainBlockContainer"] { padding: 4rem .8rem 6.8rem; }
        .service-masthead { padding: .85rem .9rem 0; border-radius: 6px 17px 6px 17px; }
        .masthead-meta { padding-bottom: .65rem; }
        .brand { padding-bottom: .8rem; }
        .brand-mark { width: 40px; height: 40px; }
        .brand-name { font-size: 1.12rem; }
        .brand-sub { font-size: .7rem; }
        .service-route { grid-template-columns: repeat(2, 1fr); margin: 0 -.9rem; }
        .route-stop:nth-child(3) { border-left: 0; border-top: 1px solid var(--line); }
        .route-stop:nth-child(4) { border-top: 1px solid var(--line); }
        .intro { grid-template-columns: 1fr; gap: .25rem; padding: 0 .08rem .72rem; }
        .intro-kicker { padding-top: 0; }
        .intro-title { font-size: 1.3rem; }
        .intro-copy { font-size: .82rem; }
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: .55rem !important; }
        [data-testid="stColumn"] {
            flex: 1 1 calc(50% - .3rem) !important;
            width: calc(50% - .3rem) !important;
            min-width: calc(50% - .3rem) !important;
        }
        [data-testid="stButton"] > button { min-height: 3.4rem; padding: .5rem .62rem; line-height: 1.35; }
        [data-testid="stChatMessage"] { padding: .9rem .85rem; }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) { margin-left: 5%; }
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            scroll-behavior: auto !important;
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: .01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="service-masthead" aria-label="Crate 服务台">
      <div class="masthead-meta">
        <span>CRATE / CUSTOMER DESK</span>
        <span class="online">服务在线</span>
      </div>
      <div class="brand">
        <div class="brand-mark" aria-hidden="true"><span>C</span></div>
        <div>
          <div class="brand-name">Crate 品牌智能助手</div>
          <div class="brand-sub">从选择商品到签收售后，沿一条服务路线解决</div>
        </div>
      </div>
      <div class="service-route" role="list" aria-label="服务范围">
        <span class="route-stop" role="listitem"><b>01</b>智能导购</span>
        <span class="route-stop" role="listitem"><b>02</b>订单查询</span>
        <span class="route-stop" role="listitem"><b>03</b>物流追踪</span>
        <span class="route-stop" role="listitem"><b>04</b>退货售后</span>
      </div>
    </section>
    <div class="intro">
      <div class="intro-kicker">START / 从这里开始</div>
      <div>
        <p class="intro-title">今天想解决什么？</p>
        <div class="intro-copy">直接描述需求。我会先理解问题，再决定是自然回答，还是查询商品、订单、物流与售后数据。</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

API_URL = os.getenv("CRATE_API_URL", "http://localhost:8000/api/v1/chat")

if "msgs" not in st.session_state:
    st.session_state.msgs = [
        {
            "role": "a",
            "text": "你好，我是 Crate 品牌智能助手。无论你想选商品、查订单、追物流、办退货，还是咨询其他问题，都可以直接告诉我。",
            "steps": None,
        }
    ]
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

INTENT_LABELS = {
    "order_status": "识别为订单查询",
    "shipping_tracking": "识别为物流追踪",
    "return_request": "识别为退货请求",
    "return_policy": "识别为退货政策咨询",
    "product_discovery": "识别为智能导购需求",
    "general": "识别为一般咨询",
}

TOOL_LABELS = {
    "lookup_order": "按订单号查询订单",
    "lookup_orders_by_email": "按邮箱查询全部订单",
    "search_orders": "模糊搜索订单与商品",
    "search_product_catalog": "搜索商品目录并按预算筛选",
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

    with st.expander("执行记录 · Tool Results", expanded=False):
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
        response = requests.post(
            API_URL,
            json={"message": query, "session_id": st.session_state.session_id},
            timeout=90,
        )
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
    ("查订单 · ORD-1002", "查询订单 ORD-1002 的状态"),
    ("追物流 · FDX-78901234", "查询物流 FDX-78901234"),
    ("选商品 · 预算 $150", "我想买一款 150 美元以内的键盘，请帮我推荐"),
    ("看政策 · 14 天退货", "请介绍一下退货政策"),
]

st.markdown('<div class="quick-label">QUICK ROUTES / 常用任务</div>', unsafe_allow_html=True)
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

if prompt := st.chat_input("想选商品、查订单，或聊点别的？直接告诉我…"):
    render_exchange(prompt)
