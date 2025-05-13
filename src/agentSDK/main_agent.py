from pydantic import BaseModel
from agents import Agent, Runner
import asyncio
import mcp.types as types

main_agent = Agent(
    name="Main Agent",
    instructions="some text",
    model="gpt-4.1-mini",
    tools=[],
    mcp_servers=[]
)







