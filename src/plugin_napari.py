import napari
from pymmcore_plus import CMMCorePlus
from mcp_server_gui import MCPServer


def main():


    viewer = napari.Viewer()
    mmc = CMMCorePlus.instance()

    main_window = MCPServer()
    viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")
    viewer.window.add_dock_widget(widget=main_window, name="MCP Server")

    # start loop
    napari.run()


if __name__ == "__main__":
    main()

