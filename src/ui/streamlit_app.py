"""
Crate — AI Support Agent
Production-grade customer support interface.
"""
import streamlit as st
import requests

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Crate Support Agent",
    page_icon="●",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Professional Styling ─────────────────────────────────────
st.markdown(
    """<style>
    /* Clean base */
    .stApp { background: #f8f9fa; }
    .main .block-container { max-width: 800px; padding-top: 1.5rem; }

    /* Hide Streamlit branding */
    #MainMenu, footer, header [data-testid="stDecoration"],
    [data-testid="stToolbar"], .stDeployButton { display: none !important; }

    /* Header */
    .brand { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
    .brand-dot { width: 10px; height: 10px; border-radius: 50%; background: #4f46e5; }
    .brand-name { font-size: 1.25rem; font-weight: 700; color: #1e1b4b; letter-spacing: -0.3px; }
    .brand-sub { font-size: 0.8rem; color: #6b7280; margin-top: -2px; margin-bottom: 20px; }

    /* Chat bubbles */
    [data-testid="stChatMessage"] { border-radius: 12px; padding: 12px 16px; margin: 8px 0; }
    [data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] { display: none; }
    .stChatMessage:has([data-testid="stChatMessageContent"] :first-child) {
        background: #ffffff; border: 1px solid #e5e7eb; box-shadow: 0 1px 2px rgba(0,0,0,.04);
    }

    /* Quick actions */
    .stButton > button {
        border-radius: 8px; border: 1px solid #d1d5db; background: #fff;
        font-size: 0.82rem; color: #374151; padding: 8px 12px;
        transition: all .15s;
    }
    .stButton > button:hover { border-color: #4f46e5; color: #4f46e5; background: #f5f3ff; }

    /* Expander */
    .streamlit-expanderHeader { font-size: 0.82rem; color: #6b7280; }
    .streamlit-expanderHeader:hover { color: #4f46e5; }

    /* Input */
    [data-testid="stChatInput"] textarea { border-radius: 10px; border: 1px solid #d1d5db; }
    </style>""",
    unsafe_allow_html=True,
)

# ── Header ───────────────────────────────────────────────────
st.markdown(
    '<div class="brand"><div class="brand-dot"></div>'
    '<span class="brand-name">Crate</span></div>'
    '<div class="brand-sub">AI-powered order &amp; shipping assistance</div>',
    unsafe_allow_html=True,
)

API_URL = "http://localhost:8000/api/v1/chat"

# ── Session ──────────────────────────────────────────────────
if "msgs" not in st.session_state:
    st.session_state.msgs = [
        {"role": "a", "text": "Hello! I'm your AI support agent. I can help you track orders, check shipments, and process returns.\n\nHow can I help you today?", "steps": None}
    ]
if "pq" not in st.session_state:
    st.session_state.pq = None

INTENT_LABEL = {
    "order_status": "Order status inquiry detected.",
    "shipping_tracking": "Package tracking request detected.",
    "return_request": "Return request detected.",
    "return_policy": "Return policy question detected.",
    "general": "General inquiry.",
}
TOOL_LABEL = {
    "lookup_order": "Queried order management system.",
    "lookup_orders_by_email": "Searched orders by customer email.",
    "search_orders": "Ran cross-order search.",
    "track_shipment": "Pulled live tracking from carrier.",
    "get_return_policy": "Retrieved return policy details.",
    "check_return_eligibility": "Checked return window & status.",
    "initiate_return": "Created RMA & initiated return.",
}


def thinking_text(steps):
    if not steps:
        return ""
    intent = steps.get("intent", "general")
    lines = [f"●  {INTENT_LABEL.get(intent, 'Analyzed the request.')}"]
    parts = []
    if steps.get("order_id"):
        parts.append(f"#{steps['order_id']}")
    if steps.get("tracking_number"):
        parts.append(steps["tracking_number"])
    if parts:
        lines.append(f"   Identified: {', '.join(parts)}")
    tools = steps.get("tool_results", {})
    if tools:
        for tn in tools:
            lines.append(f"●  {TOOL_LABEL.get(tn, 'Gathered data.')}")
    return "\n".join(lines)


def call_api(query):
    try:
        r = requests.post(API_URL, json={"message": query}, timeout=90)
        if r.status_code == 200:
            d = r.json()
            reply = d.get("response", "Sorry, something went wrong.")
            steps = {k: d.get(k, "") for k in ["intent", "order_id", "tracking_number", "customer_email"]}
            steps["tool_results"] = d.get("tool_results", {})
            return reply, steps
        return f"API error ({r.status_code}). Please try again.", None
    except requests.exceptions.ConnectionError:
        return "**Cannot reach the server.** Start it with `uvicorn src.main:app --reload`.", None
    except Exception as e:
        return f"Error: {e}", None


# ── Quick Actions ────────────────────────────────────────────
actions = [
    ("Track ORD-1002", "What's the status of order ORD-1002?"),
    ("Shipment FDX-78901234", "Where is package FDX-78901234?"),
    ("Return Policy", "What is your return policy?"),
    ("My Orders", "Show orders for james@example.com"),
]
cols = st.columns(4)
for i, (label, query) in enumerate(actions):
    with cols[i]:
        if st.button(label, use_container_width=True, key=f"qa_{i}"):
            st.session_state.pq = query
            st.rerun()
st.divider()

# ── Chat History ─────────────────────────────────────────────
for m in st.session_state.msgs:
    with st.chat_message("assistant" if m["role"] == "a" else "user"):
        if m["role"] == "a" and m.get("steps"):
            tt = thinking_text(m["steps"])
            if tt:
                with st.expander("Details", expanded=False):
                    st.markdown(f"```\n{tt}\n```")
        st.markdown(m["text"])

# ── Handle Quick-Query ───────────────────────────────────────
if st.session_state.pq:
    q = st.session_state.pq
    st.session_state.pq = None
    st.session_state.msgs.append({"role": "u", "text": q, "steps": None})
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            reply, steps = call_api(q)
        if steps:
            tt = thinking_text(steps)
            if tt:
                with st.expander("Details", expanded=False):
                    st.markdown(f"```\n{tt}\n```")
        st.markdown(reply)
        st.session_state.msgs.append({"role": "a", "text": reply, "steps": steps})
    st.rerun()

# ── Chat Input ───────────────────────────────────────────────
if prompt := st.chat_input("Type your message…"):
    st.session_state.msgs.append({"role": "u", "text": prompt, "steps": None})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            reply, steps = call_api(prompt)
        if steps:
            tt = thinking_text(steps)
            if tt:
                with st.expander("Details", expanded=False):
                    st.markdown(f"```\n{tt}\n```")
        st.markdown(reply)
        st.session_state.msgs.append({"role": "a", "text": reply, "steps": steps})
