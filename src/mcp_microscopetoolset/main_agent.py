# main_agent.py
import asyncio
import json
import uuid
from mcp_microscopetoolset.mcp_orchestrator import mcp_orchestrator

class MainAgent:
    def __init__(self):
        self.mcp_server = mcp_orchestrator
        self.session_id = "new" # Signal to the server to create a new session initially
        self._is_conversation_final = False
        self._final_output_content = None
        print(f"Client MainAgent initialized. Will request new session on first query.")

    async def process_query(self, user_query: str) -> str:
        """
        Sends the user's query to the server's high-level tool and returns the AI's response.
        """
        try:

            server_response = await self.mcp_server.call_tool(
                name="process_user_request",
                arguments={
                    "session_id": self.session_id,
                    "user_input": user_query
                }
            )
            #print(server_response[0])
            server_response = json.loads(server_response[0].text)

            self.session_id = server_response.get("session_id", self.session_id)
            self._is_conversation_final = server_response.get("is_conversation_final", False)
            self._final_output_content = server_response.get("final_output_content")

            return server_response.get("response_for_user", "An error occurred on the server.")

        except Exception as e:
            #print(e)
            #print(f"Error communicating with MCP server: {e}")
            return f"I'm sorry, an error occurred while processing your request: {e}"

    def reset_conversation(self):
        """Resets the conversation by requesting a new session ID from the server."""
        self.session_id = "new" # Signal to the server to create a new session
        self._is_conversation_final = False
        self._final_output_content = None


    def is_conversation_complete(self) -> bool:
        """Checks if the current conversation is marked as complete by the server."""
        return self._is_conversation_final

    def get_final_output(self) -> str:
        """Retrieves the final output from the server's response."""
        return self._final_output_content if self._final_output_content is not None else "No final output."