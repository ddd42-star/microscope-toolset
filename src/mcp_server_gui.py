import os
import signal

from PyQt6.QtCore import Qt, QObject, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from mcp_microscopetoolset.server_setup import run_server
from mcp.server.fastmcp import FastMCP


class MCPWorker(QObject):
    start_thread = pyqtSignal()
    stop_thread = pyqtSignal()
    def __init__(self, mcp_worker_server_object: FastMCP):
        super().__init__()
        self._mcp_worker_server_object = mcp_worker_server_object

    @pyqtSlot()
    def run_mcp_server(self):
        """
        Start the MCP server
        """
        try:
            print(os.getpid())
            #self.run_server.run(transport="streamable-http")
            run_server(self._mcp_worker_server_object)
        except Exception as e:
            print(f"Error:{e}")
        finally:
            self.stop_thread.emit()
    @pyqtSlot()
    def stop_mcp_server(self):
        """
        Stop MCP Server
        """
        print("STOP MCP Server called")
        os.kill(os.getpid(), signal.SIGINT)


class MCPServer(QMainWindow):

    def __init__(self, mcp_server_object: FastMCP):
        super().__init__()
        self.mmc = None
        self.viewer = None
        self._mcp_server_object = mcp_server_object

        # ---GUI----
        self.setObjectName("MCPServer")
        self.resize(200,100)

        self.setWindowTitle("MCP Server - Microscope Toolset")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        self.start_button = QPushButton()
        self.start_button.setText("Start Server")
        self.start_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; border-radius: 8px; padding: 10px 20px; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )
        self.stop_button = QPushButton()
        self.stop_button.setText("Stop Server")
        self.stop_button.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; border-radius: 8px; padding: 10px 20px; }"
            "QPushButton:hover { background-color: #da190b; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )

        label_title = QLabel()
        label_title.setText("Microscope Toolset MCP Server")

        # add components
        main_layout.addWidget(label_title)
        main_layout.addWidget(self.start_button,alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.stop_button,alignment=Qt.AlignmentFlag.AlignCenter)

        # connect signals
        self.start_button.clicked.connect(self.click_start_server)
        self.stop_button.clicked.connect(self.click_stop_server)
        # at the start don't show the button
        self.stop_button.setEnabled(False)

        # QThread
        self.mcp_thread = QThread()
        self.mcp_worker = MCPWorker(mcp_worker_server_object=self._mcp_server_object)

        self.mcp_worker.moveToThread(self.mcp_thread)

        self.mcp_thread.started.connect(self.mcp_worker.run_mcp_server)
        self.mcp_worker.stop_thread.connect(self.mcp_thread.quit)
        self.mcp_thread.finished.connect(self.mcp_worker.stop_mcp_server)


    def click_start_server(self):
        # hide button
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # start server
        self.mcp_thread.start()

    def click_stop_server(self):
        self.stop_button.setEnabled(False)
        self.mcp_worker.stop_mcp_server()
        self.start_button.setEnabled(True)
        self.mcp_thread.quit()