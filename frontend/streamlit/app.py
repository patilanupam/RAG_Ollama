"""
app.py — Counsellor Expert chat UI.
"""

import streamlit as st
import tempfile
import os
from datetime import datetime
from pathlib import Path

from rag.ingestion import load_document
from rag.chunker import chunk_documents
from rag.embedder import embed_texts
from rag.vectorstore import add_chunks, collection_count, clear_collection
from rag.retriever import retrieve
from rag.generator import generate_answer

st.set_page_config(page_title="Counsellor Expert", page_icon="🧠", layout="wide")

# ── Custom CSS — Hike-style messaging ─────────────────────────────────────────
st.markdown("""
<style>
/* ── Page background ── */
.stApp { background: #f0f2f5; }

/* ── Hide default streamlit header ── */
header[data-testid="stHeader"] { background: transparent; }

/* ── Chat header bar ── */
.chat-header {
    background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
    color: white;
    padding: 14px 20px;
    border-radius: 16px 16px 0 0;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.chat-header .avatar {
    width: 44px; height: 44px;
    background: #fff3;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
}
.chat-header .info { flex: 1; }
.chat-header .name { font-size: 17px; font-weight: 700; }
.chat-header .status { font-size: 12px; opacity: 0.85; }
.chat-header .doc-count {
    background: #ffffff33;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
}

/* ── Chat container ── */
.chat-body {
    background: #fff;
    border-radius: 0 0 0 0;
    min-height: 60vh;
    padding: 16px 8px;
}

/* ── Message bubbles ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 2px 0 !important;
}

/* User bubble (right) */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, #1a73e8, #1557b0) !important;
    color: white !important;
    border-radius: 18px 4px 18px 18px !important;
    max-width: 72% !important;
    margin-left: auto !important;
    padding: 10px 14px !important;
    box-shadow: 0 1px 4px rgba(26,115,232,0.3) !important;
}

/* Assistant bubble (left) */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
    [data-testid="stChatMessageContent"] {
    background: #ffffff !important;
    color: #1a1a2e !important;
    border-radius: 4px 18px 18px 18px !important;
    max-width: 72% !important;
    margin-right: auto !important;
    padding: 10px 14px !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.10) !important;
    border: 1px solid #e8eaf0 !important;
}

/* ── Timestamp style ── */
.msg-time {
    font-size: 10px;
    color: #aaa;
    margin-top: 2px;
    text-align: right;
}

/* ── Chat input bar ── */
[data-testid="stChatInput"] {
    background: #fff !important;
    border-radius: 28px !important;
    border: 1.5px solid #d0d7e3 !important;
    padding: 4px 16px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #1a73e8 !important;
    box-shadow: 0 2px 12px rgba(26,115,232,0.15) !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #1a1a2e !important;
    color: #eee;
}
section[data-testid="stSidebar"] * { color: #eee !important; }
section[data-testid="stSidebar"] .stButton button {
    background: #1a73e8 !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: #1557b0 !important;
}
section[data-testid="stSidebar"] hr { border-color: #333 !important; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #888;
}
.empty-state .icon { font-size: 64px; margin-bottom: 16px; }
.empty-state h3 { color: #555; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar: Document Ingestion ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px'>
        <div style='font-size:42px'>🧠</div>
        <div style='font-size:18px; font-weight:700; color:#fff'>Counsellor Expert</div>
        <div style='font-size:12px; opacity:0.6; margin-top:4px'>Knowledge Base Manager</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Files in data/ folder
    DATA_DIR = Path("./data")
    data_files = sorted(DATA_DIR.glob("*")) if DATA_DIR.exists() else []
    supported_exts = {".pdf", ".md", ".markdown", ".txt"}
    data_files = [f for f in data_files if f.suffix.lower() in supported_exts]

    selected_data_files = []
    if data_files:
        st.markdown("**📁 Files in `data/` folder**")
        for f in data_files:
            if st.checkbox(f.name, key=f"data_{f.name}"):
                selected_data_files.append(f)
        st.markdown("---")

    uploaded_files = st.file_uploader(
        "Upload files (PDF / Markdown / TXT)",
        type=["pdf", "md", "markdown", "txt"],
        accept_multiple_files=True,
    )

    url_input = st.text_input("Or enter a web URL", placeholder="https://example.com", key="url_input")

    top_k = st.slider("Top-K chunks to retrieve", min_value=1, max_value=10, value=5)

    col1, col2 = st.columns(2)
    ingest_clicked = col1.button("⬆️ Ingest", use_container_width=True)
    clear_clicked = col2.button("🗑️ Clear All", use_container_width=True)

    if clear_clicked:
        clear_collection()
        st.session_state.messages = []
        st.success("Vector store and chat cleared.")

    st.markdown("---")
    st.metric("Chunks in store", collection_count())

    # ── Ingestion logic ───────────────────────────────────────────────────────
    if ingest_clicked:
        sources_to_process = []

        for f in selected_data_files:
            sources_to_process.append((str(f), f.name))

        if uploaded_files:
            for uf in uploaded_files:
                suffix = Path(uf.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uf.read())
                    sources_to_process.append((tmp.name, uf.name))

        if url_input.strip():
            sources_to_process.append((url_input.strip(), url_input.strip()))

        if not sources_to_process:
            st.warning("Select a file or enter a URL first.")
        else:
            progress = st.progress(0, text="Starting…")
            total_chunks = 0
            for idx, (src_path, display_name) in enumerate(sources_to_process):
                progress.progress(idx / len(sources_to_process), text=f"Loading {display_name}…")
                try:
                    docs = load_document(src_path)
                    chunks = chunk_documents(docs)
                    if src_path != display_name:
                        for c in chunks:
                            c["source"] = display_name
                    progress.progress(
                        (idx + 0.5) / len(sources_to_process),
                        text=f"Embedding {len(chunks)} chunks…",
                    )
                    embeddings = embed_texts([c["text"] for c in chunks])
                    total_chunks += add_chunks(chunks, embeddings)
                except Exception as e:
                    st.error(f"Error processing {display_name}: {e}")
                finally:
                    if src_path != display_name and os.path.exists(src_path):
                        os.unlink(src_path)

            progress.progress(1.0, text="Done!")
            st.success(f"✅ {total_chunks} chunks from {len(sources_to_process)} source(s).")
            st.metric("Chunks in store", collection_count())

# ── Main chat area ────────────────────────────────────────────────────────────
chunk_count = collection_count()

# Chat header
st.markdown(f"""
<div class="chat-header">
    <div class="avatar">🧠</div>
    <div class="info">
        <div class="name">Counsellor Expert</div>
        <div class="status">● Online — Your personal guidance counsellor</div>
    </div>
    <div class="doc-count">📄 {chunk_count} chunks indexed</div>
</div>
""", unsafe_allow_html=True)

# Empty state
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">💬</div>
        <h3>Start a conversation</h3>
        <p>Upload your counselling documents on the left, then ask me anything.<br>
        I remember our entire conversation — just like a real chat.</p>
    </div>
    """, unsafe_allow_html=True)

# Render full conversation history
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🧠"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        # Timestamp
        if msg.get("time"):
            st.markdown(f"<div class='msg-time'>{msg['time']}</div>", unsafe_allow_html=True)

        # Show sources & chunks only for assistant messages
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📚 Sources & Retrieved Context"):
                # Source citations
                st.markdown("**Citations**")
                for src in msg["sources"]:
                    badge = f"`[{src['index']}]`"
                    loc = f"📄 **{src['source']}**"
                    if src.get("page"):
                        loc += f" — page {src['page']}"
                    score = f"  *(relevance: {src['score']:.2%})*" if src.get("score") else ""
                    st.markdown(f"{badge} {loc}{score}")

                st.divider()

                # Retrieved chunks structured view
                st.markdown("**Retrieved Chunks**")
                for i, chunk in enumerate(msg.get("chunks", []), 1):
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.markdown(f"**Chunk {i}** · `{chunk['source']}`")
                        if chunk.get("page"):
                            c2.markdown(f"📄 Page {chunk['page']}")
                        c3.markdown(f"🎯 `{chunk['score']:.2%}`")
                        st.caption(chunk["text"][:600] + ("…" if len(chunk["text"]) > 600 else ""))

# Chat input
if prompt := st.chat_input("Type a message…"):
    now = datetime.now().strftime("%I:%M %p")
    if collection_count() == 0:
        st.warning("⚠️ No documents ingested yet. Add files via the sidebar first.")
    else:
        # Display user message
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)
            st.markdown(f"<div class='msg-time'>{now}</div>", unsafe_allow_html=True)
        st.session_state.messages.append({"role": "user", "content": prompt, "time": now})

        # Retrieve + generate
        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Thinking…"):
                chunks = retrieve(prompt, k=top_k)

            if not chunks:
                reply = "I couldn't find relevant information in the documents. Could you rephrase or upload more materials?"
                st.markdown(reply)
                st.markdown(f"<div class='msg-time'>{now}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": reply, "sources": [], "chunks": [], "time": now})
            else:
                with st.spinner("Composing response…"):
                    history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1][-10:]
                        if m["role"] in ("user", "assistant")
                    ]
                    try:
                        result = generate_answer(prompt, chunks, history=history)
                    except Exception as e:
                        err = str(e)
                        if "RESOURCE_EXHAUSTED" in err or "429" in err:
                            st.error(
                                "⚠️ **Gemini quota exhausted.** Wait ~24 hrs or set "
                                "`GEMINI_MODEL=gemini-2.5-pro` in your `.env`."
                            )
                        else:
                            st.error(f"Generation error: {e}")
                        st.stop()

                st.markdown(result["answer"])
                st.markdown(f"<div class='msg-time'>{now}</div>", unsafe_allow_html=True)

                with st.expander("📚 Sources & Retrieved Context"):
                    st.markdown("**Citations**")
                    for src in result["sources"]:
                        badge = f"`[{src['index']}]`"
                        loc = f"📄 **{src['source']}**"
                        if src.get("page"):
                            loc += f" — page {src['page']}"
                        score = f"  *(relevance: {src['score']:.2%})*" if src.get("score") else ""
                        st.markdown(f"{badge} {loc}{score}")

                    st.divider()

                    st.markdown("**Retrieved Chunks**")
                    for i, chunk in enumerate(chunks, 1):
                        with st.container(border=True):
                            c1, c2, c3 = st.columns([3, 1, 1])
                            c1.markdown(f"**Chunk {i}** · `{chunk['source']}`")
                            if chunk.get("page"):
                                c2.markdown(f"📄 Page {chunk['page']}")
                            c3.markdown(f"🎯 `{chunk['score']:.2%}`")
                            st.caption(chunk["text"][:600] + ("…" if len(chunk["text"]) > 600 else ""))

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"],
                    "chunks": chunks,
                    "time": now,
                })

