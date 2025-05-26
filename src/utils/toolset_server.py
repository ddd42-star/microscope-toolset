from pydantic import BaseModel
import asyncio
import mcp.types as types
from mcp.server import FastMCP
import os
from openai import OpenAI
from normal_LLM import llm_prompt
from dotenv import load_dotenv

# create server
toolset_server = FastMCP("Microscope Toolset")


@toolset_server.tool()
def microscope_toolset():
    """
    This tools is a Microscope Assistant. It is a multi-agent system that can interact directly with a microscope.
    """
    # Steps
    # 1. Get Information of the user for the server (Which model,API_KEY, Datasets), just ask at the start the information and then cache it
    # 2. Call the tool
    # 3. Manage to connect also with the GUI (Think about this)
    system_user_information = get_user_information()

    return None

def get_user_information() -> dict:
    """
    This function retrieves the user information from the system. Later we will add the possibility for the user to add it
    """
    user_information = {}
    # load user from the environment
    load_dotenv()

    user_information['model'] = os.getenv("model")
    user_information['api_key'] = os.getenv("API_KEY")
    user_information['database'] = os.getenv("DATABASE")

    return user_information

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


