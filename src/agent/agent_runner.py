from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from src.agent.tools import (
    append_to_note_tool,
    build_index_tool,
    create_note_tool,
    find_broken_links_tool,
    find_orphaned_notes_tool,
    get_backlinks_tool,
    list_notes_tool,
    read_note_tool,
    replace_note_content_tool,
    search_notes_tool,
)

load_dotenv()  # Load environment variables from .env file

# llm = ChatOllama(model="qwen3:1.7b", reasoning=True)

llm = ChatGroq(model="llama-3.3-70b-versatile")

tools = [
    list_notes_tool,
    read_note_tool,
    search_notes_tool,
    build_index_tool,
    get_backlinks_tool,
    find_orphaned_notes_tool,
    find_broken_links_tool,
    create_note_tool,
    replace_note_content_tool,
    append_to_note_tool,
]

system_prompt = """You are an Obsidian vault assistant.

IMPORTANT RULES:
1. You MUST use tools for ANY question about notes, files, or vault contents
2. NEVER guess or make up note contents - ALWAYS use read_note_tool first
3. Before answering "I don't know", try list_notes_tool to see available notes
4. Use build_index_tool to understand vault structure

WHEN CREATING OR UPDATING NOTES:
5. Write DETAILED, comprehensive content - not just a title or brief description
6. Include explanations, examples, formulas, and relevant details
7. Use proper Markdown formatting (headers, lists, code blocks)
8. Aim for at least 200-500 words when creating educational/informational notes
9. Structure content with sections using ## headers
"""

memory = MemorySaver()

agent = create_react_agent(
    model=llm, tools=tools, checkpointer=memory, prompt=system_prompt
)
