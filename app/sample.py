from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from core.config import get_settings


@tool
def get_current_time() -> str:
    """Return the current date and time.

    Use this when the user asks what time or date it is.
    """
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculator(expression: str) -> str:
    """Evaluate a Python math expression and return the numeric result.

    Use this for arithmetic or mathematical calculations.

    Args:
        expression: A valid Python math expression, e.g. "123 * 456"
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def main():
    settings = get_settings()

    import time

    t0 = time.perf_counter()
    model = init_chat_model(
        "gemini-2.5-flash",
        model_provider="google_genai",
        google_api_key=settings.google_api_key,
    )
    print(f"init_chat_model: {time.perf_counter() - t0:.3f}s")

    t1 = time.perf_counter()
    agent = create_agent(
        model=model,
        tools=[get_current_time, calculator],
        system_prompt="You are a helpful assistant. Answer in the same language as the user.",
    )
    print(f"create_agent:    {time.perf_counter() - t1:.3f}s")

    t2 = time.perf_counter()
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "今の時刻を教えて、それから 123 * 456 を計算して",
                }
            ]
        }
    )
    print(f"agent.invoke:    {time.perf_counter() - t2:.3f}s")

    print(response["messages"][-1].content)


if __name__ == "__main__":
    main()
