import json
import uuid

from fastapi import APIRouter
from langchain_core.messages import HumanMessage
from sse_starlette.sse import EventSourceResponse

from src.agent.agent_runner import agent
from src.api.schemas.chat_request import ChatRequest
from src.api.schemas.chat_response import ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the agent and get a response."""
    thread_id = request.thread_id or (str(uuid.uuid4()))

    config = {"configurable": {"thread_id": thread_id}}

    response = agent.invoke(
        {"messages": [HumanMessage(content=request.message)]}, config=config
    )

    last_message = response["messages"][-1]
    content = getattr(last_message, "content", str(last_message))

    return ChatResponse(response=content, thread_id=thread_id)


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream responses from the agent (for real-time UI)."""

    thread_id = request.thread_id or (str(uuid.uuid4()))
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator():
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    # Use JSON to preserve whitespace exactly
                    yield {"event": "token", "data": json.dumps(chunk.content)}

        yield {"event": "done", "data": thread_id}

    return EventSourceResponse(event_generator())
