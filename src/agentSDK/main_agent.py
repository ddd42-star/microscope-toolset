from pydantic import BaseModel
from agents import Agent
import asyncio
import mcp.types as types
from mcp.server import Server

main_agent_server = Server("Main Agent Server")


@main_agent_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="",
            description="",
            inputSchema={}
        )
    ]

@main_agent_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "tool1":
        pass

    raise ValueError(f"Tool not found: {name}")




