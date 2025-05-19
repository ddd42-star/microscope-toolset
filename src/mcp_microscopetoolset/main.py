from mcp_microscopetoolset.main_client import MCPClient

import asyncio
import sys

async def main():

    if len(sys.argv) > 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()

    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()





if __name__ == "__main__":

    import sys

    asyncio.run(main())