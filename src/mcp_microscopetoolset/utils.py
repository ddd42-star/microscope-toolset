from dotenv import load_dotenv

from mcp.types import Tool
import os

#from agentsNormal.classify_user_intent import ClassifyAgent
#from agentsNormal.structuredOutput import ClassificationAgentOutput
from src.postqrl.log_db import LoggerDB


def user_message(message):

    return {"role": "user", "content": message}


def agent_message(message: str):

    return {"role": "assistant", "content": message}

def tool_message(tool_call_id: str,tool_name: str, content: str):
    return {"role": "tool", "tool_call_id": tool_call_id,"name": tool_name, "content": content}

def _add_to_conversation(context: dict, role: str, message: str):
    """Helper to add messages to the conversation history within the context."""
    context["conversation"].append({"role": role, "content": message})

def mcp_to_openai(tool: Tool):
    """
    Transform a mcp tool into an openai function schema
    """
    return {
        "type":"function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,
            "strict": False
        }
    }

# add initialization components
def get_user_information() -> dict:
    """
    This function retrieves the user information from the system. Later we will add the possibility for the user to add it
    """
    user_information = {}
    # load user from the environment
    load_dotenv()

    user_information['model'] = os.getenv("MODEL")
    user_information['api_key'] = os.getenv("API_KEY")
    user_information['database_path'] = os.getenv("DATABASE")
    user_information['collection_name'] = os.getenv("DBNAME")
    user_information['log_collection'] = os.getenv("LOGNAME")
    user_information['cfg_file'] = os.getenv("CFGPATH")
    user_information['pdf_collection_name'] = os.getenv("PDFDB")
    user_information['micromanager_devices_collection'] = os.getenv("DEVDB")
    user_information['elastic_search_path_home'] = os.getenv("ELASTICSEARCH")
    user_information['fastmcp_server_path'] = os.getenv("FASTMCP_SERVER")

    return user_information

# def initiate_napari_micromanager():
#     """This function start the napari micromanager GUI and access the core instance"""
#
#     viewer = napari.Viewer(show=False)
#     # start the napari plugin
#     dw, mainwindow = viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")
#
#     # access the instance core
#     mmc = CMMCorePlus.instance()
#
#
#     return mmc, viewer
#
# def load_config_file(config_file: str,mmc: CMMCorePlus):
#     """This function load the config file added directly in napari micromanager"""
#     mmc.loadSystemConfiguration(fileName=config_file)
#
#     return None
#
# def is_config_loaded():
#     """This function listen to napari events has test if the configuration file has been loaded"""
#
#     return None

def logger_database_exists(logger: LoggerDB, name: str) -> bool:
    """
    This function check if a logger database exists
    """

    # list the connection in the database
    list_of_collection = logger.list_collection()

    if name in list_of_collection:
        # The collection is already present
        return True
    else:
        # The collection doesn't exist
        return False
