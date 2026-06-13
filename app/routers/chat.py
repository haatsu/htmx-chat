from fastapi import APIRouter, Depends, Form
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from pydantic import BaseModel


from app.core.ai import get_model
from app.core.config import get_settings

router = APIRouter()
setting = get_settings()


class Item(BaseModel):
    message: str


@router.post("/chat")
async def chat(body: Item, model=Depends(get_model)):
    agent = create_agent(
        model=model,
        system_prompt="You are a helpful assistant. Answer in the same language as the user.",
    )

    response = agent.invoke({"messages": [HumanMessage(content=body.message)]})

    print(response["messages"][-1].content)

    return {"response": response["messages"][-1].content}


@router.post("/chat/form")
async def chat_form(message: str = Form(...), model=Depends(get_model)):
    agent = create_agent(
        model=model,
        system_prompt="You are a helpful assistant. Answer in the same language as the user.",
    )

    response = agent.invoke({"messages": [HumanMessage(content=message)]})

    return {"response": response["messages"][-1].content}
