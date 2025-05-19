import asyncio
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
from typing import Optional
from contextlib import AsyncExitStack


class MCPClient:


    def __init__(self):
        self.session = Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = OpenAI()

    async def connect_to_server(self, server: str):

        is_python = server.endswith('.py')
        if not is_python:
            raise ValueError("Server script must be .py")

        command = "python"

        server_params = StdioServerParameters(
            command=command,
            args=[server],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server))
        self.stdio, self.write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools

        print("\n Connected to server with tools: ", [tool.name for tool in tools])

    async def process_query(self, query: str):

        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()

        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        }for tool in response.tools]

        # initiate openai
        response = self.openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=2000,
            tools=available_tools
        )

        final_text = []

        assistant_message_content = []

        for content in response.choices[0].message:

            assistant_message_content.append(content)

            # adjust this part
            result = self.session.call_tool("tools") # add tool to call
            final_text.append(result)

            messages.append({
                "role": "assistant",
                "content": assistant_message_content
            })

            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "top_result",
                        "tool_use_id": content.id,
                        "content": result.content
                    }
                ]
            })

            response = self.openai.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                tools=available_tools
            )

            final_text.append(response.choices[0].message.content)

        return "\n".join(final_text)

    async def chat_loop(self):

        print("MCP Client started")
        print("Type queries or type 'quit'")

        while True:

            try:
                query = input("Digit your questions here: ").strip()

                if query.lower() == 'quit':
                    break

                response = await  self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()


