"""
app.py — The Streamlit web UI for whatdoIeat

WHY STREAMLIT:
Streamlit turns Python scripts into web apps with zero HTML/CSS/JS.
Perfect for Data Engineers — you already know Python, no frontend skills needed.
One command to run locally, one command to deploy.

HOW STREAMLIT WORKS:
Every time the user interacts (types a message, clicks a button), the entire
script re-runs from top to bottom. Streamlit's `st.session_state` is how you
persist data (like chat history) across those re-runs.

RUN WITH:
    streamlit run app.py

WHAT YOU'LL SEE:
- A chat interface with message bubbles
- Bot responses with the retrieval strategy shown underneath
- A sidebar with restaurant info and quick-question buttons
- A debug toggle to see which chunks were retrieved
"""

import streamlit as st
import sys
from pathlib import Path

# Add src/ to path so we can import chain.py
sys.path.insert(0, str(Path(__file__).parent / "src"))
from chain import ask

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="whatdoIeat — Sangam Chettinad",
    page_icon="🍛",
    layout="centered",
)

# ── Session state init ────────────────────────────────────────────────────────
# WHY session_state?
# Streamlit re-runs the whole script on every interaction.
# session_state persists values across re-runs — without it,
# chat history would reset every time the user types a message.
if "messages" not in st.session_state:
    st.session_state.messages = []          # displayed chat bubbles
if "history" not in st.session_state:
    st.session_state.history = []           # LLM conversation history
if "last_chunks" not in st.session_state:
    st.session_state.last_chunks = []       # last retrieved chunks for debug
if "last_strategy" not in st.session_state:
    st.session_state.last_strategy = ""

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🍛 Sangam Chettinad")
    st.caption("Authentic South Indian & Chettinad Cuisine")
    st.markdown("📍 6001 W Parmer Ln, Austin TX")
    st.markdown("📞 +1 512-770-1104")

    st.divider()
    st.subheader("Hours")
    st.markdown("""
    **Weekdays**
    Lunch: 11:30 AM – 2:30 PM
    Dinner: 5:30 PM – 10:00 PM

    **Weekends**
    Breakfast: 8:30 – 10:00 AM
    Lunch: 12:00 – 3:00 PM
    Dinner: 5:30 – 10:00 PM
    """)

    st.divider()
    st.subheader("Try asking:")

    # Quick question buttons — clicking one sends it as a message
    quick_questions = [
        "What should I order for the first time?",
        "Any vegetarian options under $12?",
        "What do people say about this place?",
        "Something good for someone who loves spice?",
        "Do you have anything vegan?",
    ]

    for q in quick_questions:
        if st.button(q, use_container_width=True):
            st.session_state.quick_question = q

    st.divider()
    show_debug = st.toggle("Show retrieved chunks", value=False)

    if st.button("🗑 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.last_chunks = []
        st.session_state.last_strategy = ""
        st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("🍛 whatdoIeat?")
st.caption("Ask me anything about Sangam Chettinad Indian Cuisine in Austin, TX")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and show_debug and msg.get("strategy"):
            st.caption(f"🔍 Strategy: {msg['strategy']}")
            if msg.get("chunks"):
                with st.expander("Retrieved chunks"):
                    for c in msg["chunks"]:
                        chunk_type = c["metadata"].get("type", "?")
                        name = c["metadata"].get("name", c["id"])
                        sim = c["similarity"]
                        st.markdown(f"**[{chunk_type}]** {name} — sim: `{sim}`")
                        st.caption(c["text"][:200] + "...")

# ── Handle quick question from sidebar ───────────────────────────────────────
if "quick_question" in st.session_state and st.session_state.quick_question:
    prompt = st.session_state.quick_question
    st.session_state.quick_question = None
else:
    prompt = st.chat_input("Ask about the menu, hours, reviews...")

# ── Process new message ───────────────────────────────────────────────────────
if prompt:
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Finding the best answer..."):
            result = ask(prompt, st.session_state.history)

        st.markdown(result["answer"])

        if show_debug:
            st.caption(f"🔍 Strategy: {result['strategy']}")
            with st.expander("Retrieved chunks"):
                for c in result["chunks_used"]:
                    chunk_type = c["metadata"].get("type", "?")
                    name = c["metadata"].get("name", c["id"])
                    sim = c["similarity"]
                    st.markdown(f"**[{chunk_type}]** {name} — sim: `{sim}`")
                    st.caption(c["text"][:200] + "...")

    # Save to session state
    st.session_state.history = result["history"]
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "strategy": result["strategy"],
        "chunks": result["chunks_used"],
    })
    st.rerun()