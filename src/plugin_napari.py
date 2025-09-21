import napari
from src.mcp_server_gui import MCPServer
import os
import logging
import sys

#  logger
logger = logging.getLogger("Napari-MicroscopeTool")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)
fh = logging.FileHandler("microscope_toolset.log", encoding="utf-8")
fh.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
logger.addHandler(fh)


if __name__ == "__main__":
    try:
        # start napari micromanager
        logger.info("Start napari window")
        viewer = napari.Viewer()
        logger.info(viewer.window)
        logger.info("start mcp server widget")
        main_window = MCPServer()
        viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")
        viewer.window.add_dock_widget(widget=main_window, name="MCP Server", area="top", allowed_areas=["right"])

        # start loop
        napari.run()

        logger.info("Napari finished")
    except Exception as e:
        logger.info(f"Error starting napari: {e}")
