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
if "vault_path" not in st.session_state:
    st.session_state.vault_path = ""
if "vault_configured" not in st.session_state:
    st.session_state.vault_configured = False


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

        current_event = None

        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode("utf-8")

            if line.startswith("event:"):
                current_event = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data = line[len("data:") :].strip()

                if current_event == "token":
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        yield data
                elif current_event == "done":
                    break

    except requests.RequestException as e:
        yield f"API call failed: {e}"


st.title("Obsidian Vault - Chat with Agent")

with st.expander("🔧 Configure Obsidian Vault", expanded=True):
    vault_path = st.text_input(
        "Obsidian Vault Path",
        value=st.session_state.vault_path,
        placeholder="Enter the path to your Obsidian vault (e.g., /path/to/vault)",
    )

    col_set, col_status = st.columns([1, 3])

    with col_set:
        if st.button("Set vault"):
            try:
                resp = requests.post(
                    f"{API_URL}/chat/set-vault",
                    json={
                        "thread_id": st.session_state.thread_id,
                        "vault_path": vault_path,
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                st.session_state.vault_path = vault_path
                st.session_state.vault_configured = True
                st.success("Vault configured successfully!")
            except requests.RequestException as e:
                st.session_state.vault_configured = False
                st.error(f"Failed to configure vault: {e}")

    with col_status:
        if st.session_state.vault_configured:
            st.success(f"Vault is set: {st.session_state.vault_path}")
        else:
            st.info("Vault is not configured.")

col1, col2 = st.columns([4, 1])
with col2:
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.vault_configured = False
        st.session_state.vault_path = ""
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if not st.session_state.vault_configured:
    st.info("Please configure your Obsidian vault path before chatting.")
    user_input = None
else:
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
