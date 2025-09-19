import subprocess
import sys
import logging
from PyQt6.QtCore import Qt, QObject, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from src.mcp_microscopetoolset.utils import get_user_information
from src.start_subprocess.servers import _start_server,_stop_server, wait_for_es

#  logger
logger = logging.getLogger("MCPServer")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("mcp_subprocess.log", encoding="utf-8")
fh.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
logger.addHandler(fh)

class MCPWorker(QObject):
    start_thread = pyqtSignal()
    stop_thread = pyqtSignal()
    # New signals for status updates
    status_update = pyqtSignal(str)  # For status messages
    servers_ready = pyqtSignal()  # When both servers are ready
    servers_stopped = pyqtSignal()  # When both servers are stopped
    def __init__(self):
        super().__init__()
        self._elastic_search_process: subprocess.Popen = None
        self._fastmcp_process: subprocess.Popen = None

    @pyqtSlot()
    def run_mcp_server(self):
        """
        Start the MCP server
        """
        try:
            # Start Elasticsearch first
            self.status_update.emit("Loading Elasticsearch server...")

            ui = get_user_information()
            es_home = ui["elastic_search_path_home"]
            if sys.platform.startswith("win"):
                exe = f"{es_home}\\bin\\elasticsearch.bat"
            else:
                exe = f"{es_home}/bin/elasticsearch"

            logger.info(f"Launching Elasticsearch: {exe}")
            self._elastic_search_process = _start_server([exe, "-d", "-p", "pid"])
            logger.info(f"Elasticsearch server started with PID={self._elastic_search_process.pid}")

            # Wait until server has started and ping with Elasticsearch Client
            self.status_update.emit("Waiting for Elasticsearch to be ready...")
            try:
                wait_for_es(max_wait=60)
                logger.info("Elasticsearch is ready!")
            except Exception as e:
                logger.error(f"ES startup failed: {e}")
                self._elastic_search_process.terminate()
                self.status_update.emit("Elasticsearch failed to start")
                return

            # Start FastMCP server
            self.status_update.emit("Loading FastMCP server...")
            self._fastmcp_process = _start_server([sys.executable, "-m", "src.start_subprocess.fastmcp_server_script"])
            logger.info(f"FastMCP server started with PID={self._fastmcp_process.pid}")

            # Both servers are ready
            logger.info("Both processes started successfully")
            self.status_update.emit("Both servers ready! You can start VS Code or Cursor.")
            self.servers_ready.emit()

        except Exception as e:
            logger.error(f"Error starting servers: {e}")
            self.status_update.emit(f"Error: {e}")
        finally:
            self.stop_thread.emit()

    @pyqtSlot()
    def stop_mcp_server(self):
        """
        Stop the MCP server
        """
        self.status_update.emit("Stopping servers...")

        # Check if processes exist
        if self._elastic_search_process is None and self._fastmcp_process is None:
            self.status_update.emit("No servers to stop")
            self.servers_stopped.emit()
            return

        try:
            # Stop FastMCP first
            if self._fastmcp_process is not None:
                self.status_update.emit("Stopping FastMCP server...")
                _stop_server(self._fastmcp_process)
                logger.info("Stopped FastMCP")
                self._fastmcp_process = None

            # Stop Elasticsearch
            if self._elastic_search_process is not None:
                self.status_update.emit("Stopping Elasticsearch server...")
                _stop_server(self._elastic_search_process)
                logger.info("Stopped Elasticsearch")
                self._elastic_search_process = None

            logger.info("All servers stopped")
            self.status_update.emit("All servers stopped")
            self.servers_stopped.emit()

        except Exception as e:
            logger.error(f"Error stopping servers: {e}")
            self.status_update.emit(f"Error stopping servers: {e}")
            self.servers_stopped.emit()


class MCPServer(QWidget):

    def __init__(self):
        super().__init__()
        self.mmc = None
        self.viewer = None

        # ---GUI----
        self.setObjectName("MCPServer")
        self.resize(300, 150)
        self.setWindowTitle("MCP Server - Microscope Toolset")

        main_layout = QVBoxLayout(self)

        # Title label
        label_title = QLabel()
        label_title.setText("Microscope Toolset MCP Server")
        label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")

        # Status label
        self.status_label = QLabel()
        self.status_label.setText("Ready to start servers")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 15px; padding: 5px;")

        # Start button
        self.start_button = QPushButton()
        self.start_button.setText("Start Servers")
        self.start_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; border-radius: 8px; padding: 10px 20px; font-size: 12px; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )

        # Stop button
        self.stop_button = QPushButton()
        self.stop_button.setText("Stop Servers")
        self.stop_button.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; border-radius: 8px; padding: 10px 20px; font-size: 12px; }"
            "QPushButton:hover { background-color: #da190b; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )

        # Add components to layout
        main_layout.addWidget(label_title)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.stop_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Connect signals
        self.start_button.clicked.connect(self.click_start_server)
        self.stop_button.clicked.connect(self.click_stop_server)

        # Initial button states
        self.stop_button.setEnabled(False)

        # QThread setup
        self.mcp_thread = QThread()
        self.mcp_worker = MCPWorker()
        self.mcp_worker.moveToThread(self.mcp_thread)

        # Connect worker signals
        self.mcp_thread.started.connect(self.mcp_worker.run_mcp_server)
        self.mcp_worker.stop_thread.connect(self.mcp_thread.quit)

        # Connect status update signals
        self.mcp_worker.status_update.connect(self.update_status_label)
        self.mcp_worker.servers_ready.connect(self.on_servers_ready)
        self.mcp_worker.servers_stopped.connect(self.on_servers_stopped)

    def click_start_server(self):
        """Handle start button click"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)  # Disable until servers are ready
        self.status_label.setText("Starting servers...")
        self.mcp_thread.start()

    def click_stop_server(self):
        """Handle stop button click"""
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.status_label.setText("Stopping servers...")
        self.mcp_worker.stop_mcp_server()
        self.mcp_thread.quit()

    @pyqtSlot(str)
    def update_status_label(self, message):
        """Update the status label with current operation"""
        self.status_label.setText(message)

        # Change color based on message content
        if "ready" in message.lower() or "you can start" in message.lower():
            self.status_label.setStyleSheet(
                "font-size: 12px; color: #4CAF50; margin-bottom: 15px; padding: 5px; font-weight: bold;")
        elif "error" in message.lower() or "failed" in message.lower():
            self.status_label.setStyleSheet(
                "font-size: 12px; color: #f44336; margin-bottom: 15px; padding: 5px; font-weight: bold;")
        elif "loading" in message.lower() or "starting" in message.lower() or "stopping" in message.lower() or "waiting" in message.lower():
            self.status_label.setStyleSheet(
                "font-size: 12px; color: #FF9800; margin-bottom: 15px; padding: 5px; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 15px; padding: 5px;")

    @pyqtSlot()
    def on_servers_ready(self):
        """Called when both servers are ready"""
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)

    @pyqtSlot()
    def on_servers_stopped(self):
        """Called when both servers are stopped"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Ready to start servers")

    def closeEvent(self, event):
        """Handle window close event"""
        self.hide()
        event.ignore()
        print("MCP Server window closed")