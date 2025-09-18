import signal
import threading

import napari
from napari_plugin_engine import napari_hook_implementation
from pymmcore_plus import CMMCorePlus
from mcp_server_gui import MCPServer
from mcp_tool_new_version import build_server
from start_elastic_search import start_elastic_search
import os
from mcp_microscopetoolset.server_setup import create_mcp_server
from mcp_microscopetoolset.agents_init import initialize_agents


if __name__ == "__main__":
    try:
        # start the elasticsearch db into a new thread
        threading.Thread(name="elastic search", target=start_elastic_search, daemon=True).start()
        print("current pid", os.getpid())
        # start napari micromanager
        print("Start napari window")
        viewer = napari.Viewer()
        print(viewer)
        #mmc = CMMCorePlus.instance()
        print("start mcp server")
        #mcp_run_server = build_server()
        agents_initialization = initialize_agents()
        mcp_run_server = create_mcp_server(database_agent=agents_initialization["database_agent"],
                                           microscope_status=agents_initialization["microscope_status"],
                                           no_coding_agent=agents_initialization["no_coding_agent"],
                                           executor=agents_initialization["executor"],
                                           logger_agent=agents_initialization["logger_agent"]
                                           )
        print(mcp_run_server)
        main_window = MCPServer(mcp_server_object=mcp_run_server)
        viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")
        #viewer.window.add_plugin_dock_widget(plugin_name="MCP Server", widget_name=main_window)
        viewer.window.add_dock_widget(widget=main_window, name="MCP Server")

        # start loop
        napari.run()

        print("Napari finished")

        # kill the es process
        # read es pid
        with open("./tmp_es_pid.txt", "r") as f:
            tmp_es_pid = int(f.read())
        print(f"es server pid {tmp_es_pid}")
        os.kill(tmp_es_pid, signal.SIGTERM)
        # delete tmp file where the pid was saved
        os.remove("./tmp_es_pid.txt")
    except Exception as e:
        print(f"Error starting napari: {e}")
# Register MCPServer as a dock widget plugin
# @napari_hook_implementation
# def napari_experimental_provide_dock_widget():
#     def widget_factory():
#         # Initialize agents and server only once per widget instance
#         agents_initialization = initialize_agents()
#         mcp_run_server = create_mcp_server(
#             database_agent=agents_initialization["database_agent"],
#             microscope_status=agents_initialization["microscope_status"],
#             no_coding_agent=agents_initialization["no_coding_agent"],
#             executor=agents_initialization["executor"],
#             logger_agent=agents_initialization["logger_agent"]
#         )
#         return MCPServer(mcp_server_object=mcp_run_server)
#     return [(widget_factory, {"name": "MCP Server"})]
#
# if __name__ == "__main__":
#     try:
#         # start the elasticsearch db into a new thread
#         threading.Thread(name="elastic search", target=start_elastic_search, daemon=True).start()
#         print("current pid", os.getpid())
#         # start napari viewer
#         print("Start napari window")
#         viewer = napari.Viewer()
#         print(viewer)
#         # Add napari-micromanager dock widget if needed
#         #viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")
#         napari.run()
#         print("Napari finished")
#         # kill the es process
#         with open("./tmp_es_pid.txt", "r") as f:
#             tmp_es_pid = int(f.read())
#         print(f"es server pid {tmp_es_pid}")
#         os.kill(tmp_es_pid, signal.SIGTERM)
#         os.remove("./tmp_es_pid.txt")
#     except Exception as e:
#         print(f"Error starting napari: {e}")
