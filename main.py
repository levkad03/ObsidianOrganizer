import uuid

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langfuse.langchain import CallbackHandler

from src.agent import agent

st.set_page_config(page_title="Obsidian Vault Agent — Chat", layout="centered")

load_dotenv()


@st.cache_resource
def get_langfuse_handler():
    return CallbackHandler(update_trace=True)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())


def call_agent(user_text):
    config = {
        "configurable": {"thread_id": st.session_state.thread_id},
        "callbacks": [get_langfuse_handler()],  # Add this line
    }

    try:
        resp = agent.invoke(
            {"messages": [HumanMessage(content=user_text)]}, config=config
        )
    except Exception as e:
        return f"Agent call failed: {e}"

    if isinstance(resp, dict) and "messages" in resp:
        last = resp["messages"][-1]
        return getattr(
            last,
            "content",
            last.get("content") if isinstance(last, dict) else str(last),
        )
    return str(resp)


st.title("Obsidian Vault - Chat with Agent")

col1, col2 = st.columns([4, 1])
with col2:
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

for msg in st.session_state.messages:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    if role == "system":
        st.markdown(f"*System:* {content}")
    else:
        with st.chat_message(role):
            st.markdown(content)

user_input = st.chat_input("Ask about notes, folders, or update/create actions...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            assistant_text = call_agent(user_input)
            st.markdown(assistant_text)

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
