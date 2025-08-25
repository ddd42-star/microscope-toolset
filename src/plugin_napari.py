import signal
import threading

import napari
from pymmcore_plus import CMMCorePlus
from mcp_server_gui import MCPServer
from mcp_tool_new_version import build_server
from start_elastic_search import start_elastic_search
import os


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
        mcp_run_server = build_server()
        print(mcp_run_server)
        main_window = MCPServer(run_server=mcp_run_server)
        viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")
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

