from pydantic import BaseModel
import asyncio
import mcp.types as types
from mcp.server import FastMCP
import os
from openai import OpenAI
from normal_LLM import llm_prompt

# create server
toolset_server = FastMCP("Microscope Toolset")


@toolset_server.tool()
def microscope_toolset():

    return None



@toolset_server.tool()
def search_articles():

    return None


@toolset_server.tool()
def llm(user_input: str):
    """
    This tools is a simple agent that helps the user in any types of questions and requests

    Input:
        user_input: str
            Represent the user's question or request
    Output:
        A plane text string containing the API call of the agent.
    """
    openai_key = os.getenv("OPENAI_API_KEY")

    client = OpenAI(api_key=openai_key)

    prompt = llm_prompt

    history = [{"role": "system", "content": prompt}, {"role": "user", "content": user_input}]

    try:

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=history
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error communicating with LLM: {e}"


if __name__ == "__main__":
    # Initialize and run the server
    toolset_server.run(transport='stdio')


