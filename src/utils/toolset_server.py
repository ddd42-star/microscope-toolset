from pydantic import BaseModel
import asyncio
import mcp.types as types
from mcp.server import FastMCP

# create server
toolset_server = FastMCP("Microscope Toolset")


@toolset_server.tool()
def microscope_toolset():

    return None



@toolset_server.tool()
def search_articles():

    return None


@toolset_server.tool()
def llm():


    return None


if __name__ == "__main__":
    # Initialize and run the server
    toolset_server.run(transport='stdio')


