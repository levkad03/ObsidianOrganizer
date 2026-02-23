from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from src.agent.tools import (
    append_to_note_tool,
    create_note_tool,
    find_broken_links_tool,
    find_orphaned_notes_tool,
    find_similar_notes_tool,
    get_backlinks_tool,
    list_notes_tool,
    read_note_tool,
    replace_note_content_tool,
    search_notes_tool,
    semantic_search_tool,
    suggest_connections_by_graph_tool,
    suggest_connections_by_keywords_tool,
    suggest_connections_by_tags_tool,
)

load_dotenv()  # Load environment variables from .env file

# llm = ChatOllama(model="qwen3:1.7b", reasoning=True)

llm = ChatGroq(model="openai/gpt-oss-20b")

tools = [
    list_notes_tool,
    read_note_tool,
    search_notes_tool,
    get_backlinks_tool,
    find_orphaned_notes_tool,
    find_broken_links_tool,
    create_note_tool,
    replace_note_content_tool,
    append_to_note_tool,
    suggest_connections_by_tags_tool,
    suggest_connections_by_keywords_tool,
    suggest_connections_by_graph_tool,
    find_similar_notes_tool,
    semantic_search_tool,
]

system_prompt = """You are an Obsidian vault assistant. Always use tools — never guess note contents.

Tool selection guide:
- Exact word/tag search → search_notes_tool
- Conceptual/vague search → semantic_search_tool  
- Note structure/links → build_index_tool
- Single note content → read_note_tool

When writing notes: use ## headers, 200-500 words, include examples and formulas."""

memory = MemorySaver()

agent = create_react_agent(
    model=llm, tools=tools, checkpointer=memory, prompt=system_prompt
)
