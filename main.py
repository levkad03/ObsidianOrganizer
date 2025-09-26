import streamlit as st

from src.agent.agent_runner import agent

st.set_page_config(page_title="Obsidian Vault Agent — Chat", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are an assistant for an Obsidian vault."}
    ]


def call_agent(messages, user_text):
    # Try common agent call patterns and fall back to plain text run
    config = {"configurable": {"thread_id": "my-conversation"}}
    try:
        resp = agent.invoke({"messages": messages}, config=config)
    except Exception as e:
        return f"Agent call failed: {e}"

    # Normalize response shape to a string
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
        st.session_state.messages = [
            {
                "role": "system",
                "content": "You are an assistant for an Obsidian vault.",
            }
        ]
        st.rerun()

# render chat history
for msg in st.session_state.messages:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    if role == "system":
        st.markdown(f"*System:* {content}")
    else:
        with st.chat_message(role):
            st.markdown(content)

# chat input
user_input = st.chat_input("Ask about notes, folders, or update/create actions...")

if user_input:
    # display and store user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # call agent and display assistant reply
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            assistant_text = call_agent(st.session_state.messages, user_input)
            st.markdown(assistant_text)

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
