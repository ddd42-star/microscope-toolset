import napari
from mcp_gui import MCPWindow

def main():
    # call new napari viewer
    viewer = napari.Viewer()

    main_window = MCPWindow()

    # call the plugins
    viewer.window.add_plugin_dock_widget("napari-micromanager")
    viewer.window.add_dock_widget(main_window)

    # start loop for gui interaction
    napari.run()

if __name__ == "__main__":
    main()



