from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from src.agent.tools import (
    build_index_tool,
    list_notes_tool,
    read_note_tool,
    write_note_tool,
)

llm = ChatOllama(model="qwen3:1.7b", reasoning=False)

tools = [list_notes_tool, read_note_tool, write_note_tool, build_index_tool]

agent = create_react_agent(model=llm, tools=tools)
