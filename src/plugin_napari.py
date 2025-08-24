import threading

import napari
from pymmcore_plus import CMMCorePlus
from mcp_server_gui import MCPServer
from mcp_tool_new_version import build_server
from start_elastic_search import start_elastic_search


def main():

    try:

        # start the elasticsearch db into a new thread
        threading.Thread(name="elastic search", target=start_elastic_search, daemon=True).start()
        # start napari micromanager
        viewer = napari.Viewer()
        #mmc = CMMCorePlus.instance()
        mcp_run_server = build_server()

        main_window = MCPServer(run_server=mcp_run_server)
        viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")
        viewer.window.add_dock_widget(widget=main_window, name="MCP Server")

        # start loop
        napari.run()
    except Exception as e:
        return f"Error starting napari: {e}"


if __name__ == "__main__":
    main()

