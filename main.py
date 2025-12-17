import json
import uuid

import requests
import streamlit as st
from dotenv import load_dotenv

API_URL = "http://localhost:8000"


st.set_page_config(page_title="Obsidian Vault Agent — Chat", layout="centered")

load_dotenv()


if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())


def stream_response(user_text: str):
    """Stream response from the API using SSE."""

    try:
        response = requests.post(
            f"{API_URL}/chat/stream",
            json={"message": user_text, "thread_id": st.session_state.thread_id},
            stream=True,
            timeout=120,
        )

        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                # Parse SSE format: "event: type" and "data: content"
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data and data != "[DONE]":
                        try:
                            # Data is JSON encoded to preserve whitespace
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            yield data
    except requests.RequestException as e:
        yield f"API call failed: {e}"


st.title("Obsidian Vault - Chat with Agent")

col1, col2 = st.columns([4, 1])
with col2:
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask about notes, folders, or update/create actions...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        for chunk in stream_response(user_input):
            full_response += chunk
            response_placeholder.markdown(full_response + "▌")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
