import sys
import subprocess
from PyQt6.QtCore import Qt, QObject, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QApplication


class MCPWorker(QObject):
    start_thread = pyqtSignal()
    stop_thread = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.result = None
    @pyqtSlot()
    def run_mcp_server(self):
        self.start_thread.emit()
        self.result = subprocess.Popen(args=["python", 'C:\\Users\\dario\\OneDrive\\università\\MA\\Thesis\\microscope-toolset\\microscope-toolset\\src\\mcp_tool_new_version.py'], stdout=subprocess.PIPE)

    @pyqtSlot()
    def stop_mcp_server(self):
        self.result.terminate()
        self.stop_thread.emit()



class MCPServer(QMainWindow):

    def __init__(self):
        super().__init__()
        self.mmc = None
        self.viewer = None

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
        self.mcp_worker = MCPWorker()

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

