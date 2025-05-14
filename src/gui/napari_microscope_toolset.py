import napari
from mcp_gui import MCPWindow, LLM

def main():
    # call new napari viewer
    viewer = napari.Viewer()

    #main_window = MCPWindow()
    client = LLM()
    # Create and show the main window, passing the LLM client
    main_window = MCPWindow(client)
    #main_window.show()
    # call the plugins
    viewer.window.add_plugin_dock_widget("napari-micromanager")
    viewer.window.add_dock_widget(widget=main_window, name="llm", area="right")

    # start loop for gui interaction
    napari.run()

if __name__ == "__main__":
    main()



