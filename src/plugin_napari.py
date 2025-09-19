import napari
from src.mcp_server_gui import MCPServer
import os


if __name__ == "__main__":
    try:
        # start napari micromanager
        print("Start napari window")
        viewer = napari.Viewer()
        print(viewer)
        #mmc = CMMCorePlus.instance()
        print("start mcp server")
        main_window = MCPServer()#mcp_server_object=mcp_run_server
        viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")
        viewer.window.add_dock_widget(widget=main_window, name="MCP Server", area="top", allowed_areas=["right"])

        # start loop
        napari.run()

        print("Napari finished")
    except Exception as e:
        print(f"Error starting napari: {e}")
