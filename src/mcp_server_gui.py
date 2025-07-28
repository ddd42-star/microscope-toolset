import sys
import subprocess
import threading

from PyQt6.QtCore import Qt, QObject, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QApplication


class MCPWorker(QObject):
    start_thread = pyqtSignal()
    stop_thread = pyqtSignal()
    def __init__(self, run_server):
        super().__init__()
        self.run_server = run_server
        self.result = threading.Event()

    @pyqtSlot()
    def run_mcp_server(self):
        self.start_thread.emit()
        try:
            #self.run_server(stop_flag=self.result.is_set)
            self.run_server.run(transport="streamable-http")

            while not self.result.is_set():
                print("call me")
                QThread.msleep(100)
        finally:
            self.stop_thread.emit()
    @pyqtSlot()
    def stop_mcp_server(self):
        self.stop_thread.emit()
        self.result.set()


class MCPServer(QMainWindow):

    def __init__(self, run_server):
        super().__init__()
        self.mmc = None
        self.viewer = None
        self.run_server = run_server

        # ---GUI----
        self.setObjectName("MCPServer")
        self.resize(200,100)

        self.setWindowTitle("MCP Server - Microscope Toolset")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        self.start_button = QPushButton()
        self.start_button.setText("Start Server")
        self.stop_button = QPushButton()
        self.stop_button.setText("Stop Server")

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
        self.mcp_worker = MCPWorker(run_server=self.run_server)

        self.mcp_worker.moveToThread(self.mcp_thread)

        self.mcp_thread.started.connect(self.mcp_worker.run_mcp_server)
        self.mcp_thread.finished.connect(self.mcp_worker.stop_mcp_server)




    def click_start_server(self):
        # hide button
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # start server
        self.mcp_thread.start()

    def click_stop_server(self):
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self.mcp_thread.quit()