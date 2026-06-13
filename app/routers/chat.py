import json

from fastapi import APIRouter, Depends, Form
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from app.core.ai import get_model
from app.core.auth import get_current_user

router = APIRouter()

_checkpointer = MemorySaver()


class Item(BaseModel):
    message: str


class StreamRequest(BaseModel):
    message: str
    thread_id: str


@router.post("/chat")
async def chat(body: Item, model=Depends(get_model)):
    agent = create_agent(
        model=model,
        system_prompt="You are a helpful assistant. Answer in the same language as the user.",
    )
    response = agent.invoke({"messages": [HumanMessage(content=body.message)]})
    return {"response": response["messages"][-1].content}


@router.post("/chat/form")
async def chat_form(message: str = Form(...), model=Depends(get_model)):
    agent = create_agent(
        model=model,
        system_prompt="You are a helpful assistant. Answer in the same language as the user.",
    )
    response = agent.invoke({"messages": [HumanMessage(content=message)]})
    return {"response": response["messages"][-1].content}


@router.post("/chat/stream")
async def chat_stream(
    body: StreamRequest,
    model=Depends(get_model),
    username: str = Depends(get_current_user),
):
    agent = create_agent(
        model=model,
        system_prompt="You are a helpful assistant. Answer in the same language as the user.",
        checkpointer=_checkpointer,
    )
    config = {"configurable": {"thread_id": body.thread_id}}

    async def generate():
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=body.message)]},
            config=config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk:
                    yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
