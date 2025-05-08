import asyncio

from mcp import stdio_server
from mcp.server import Server
import mcp.types as types

app = Server("microscope-tool")

@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="example://resource",
            name="Example resource"
        )
    ]

async def main():
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )


if __name__ == "__main__":

    asyncio.run(main())