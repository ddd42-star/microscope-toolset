import napari
from gui.mcp_gui import MCPWindow, LLM, Publication
from pymmcore_plus import CMMCorePlus

def main():


    # call new napari viewer
    viewer = napari.Viewer()
    client = LLM()
    publication_client = Publication()
    mmc = CMMCorePlus.instance()

    main_window = MCPWindow(client, mmc, publication_client)
    viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")
    viewer.window.add_dock_widget(widget=main_window, name="llm", area="right")

    # start loop for gui interaction
    napari.run()

if __name__ == "__main__":
    main()



