import asyncio

from mcp.server.fastmcp import FastMCP
import threading
import napari
import multiprocessing
from pymmcore_plus import CMMCorePlus
from napari.qt.threading import thread_worker


def mcp_server():

    mcp = FastMCP(
        name="EasyServer",
        description="A simple server for easy operations",
        version="1.0.0"
    )

    @mcp.tool(
        name="addition",
        description="Sum of two parameters"
    )
    def addition(a:int, b:int):
        return a + b

    mcp.run(transport="stdio")


    #return mcp

def gui():

    viewer = napari.Viewer()

    # start the napari plugin
    dw, mainwindow = viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")

    # access the instance core
    mmc = CMMCorePlus.instance()

    napari.run()
    #return mmc, viewer


if __name__ == "__main__":
    thread1 = threading.Thread(name="mcp server", target=mcp_server)
    thread1.start()

    gui()


