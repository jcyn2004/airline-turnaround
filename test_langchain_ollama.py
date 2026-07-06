import asyncio
from langchain_ollama import ChatOllama
from langchain_core.tools import tool

@tool
def get_clearance(flight_number: str, aircraft_type: str) -> str:
    """Request landing clearance for a flight."""
    return "CLEARED_FOR_LANDING runway 19R"

async def main():
    llm = ChatOllama(model="qwen3:32b", temperature=0)
    llm_t = llm.bind_tools([get_clearance])
    resp = await llm_t.ainvoke("Flight AF84, a B747, is incoming. Request landing clearance.")
    print("tool_calls:", resp.tool_calls)
    print("content:", resp.content[:200])

asyncio.run(main())
