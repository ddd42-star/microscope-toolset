import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QScrollArea, QTextBrowser, QLineEdit, QPushButton,
                             QLabel, QComboBox)
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import os
from openai import OpenAI
import time
import markdown
from napari._qt.qt_resources import get_current_stylesheet

# --- Worker Object for LLM API Call ---
class LLMWorker(QObject):
    # Signal emitted when the LLM response is received
    response_received = pyqtSignal(str)
    # Removed the 'finished' signal here, as it's not needed for task completion notification
    # If needed for more complex state management, it would be used differently.

    def __init__(self, llm_client):
        super().__init__()
        self.llm_client = llm_client
        self.setObjectName("LLMWorker")

    @pyqtSlot(str)
    def process_message(self, user_input):
        print(f"--- Entering process_message ---")
        print(f"Current Thread (process_message): {QThread.currentThread().objectName()} (ID: {int(QThread.currentThreadId())})")
        print(f"Worker Object's Thread Affinity: {self.thread().objectName() if self.thread() else 'None'} (ID: {int(self.thread().currentThreadId()) if self.thread() else 'None'})")

        try:
            print(f"Worker Thread ({QThread.currentThread().objectName()}): Sending message to LLM...")
            # This is the long-running operation
            response = self.llm_client.message(user_input)
            print(f"Worker Thread ({QThread.currentThread().objectName()}): Received response from LLM.")
            # Emit the signal with the response to be handled in the main thread
            self.response_received.emit(response)
        except Exception as e:
            print(f"Worker Thread ({QThread.currentThread().objectName()}): An error occurred during LLM call: {e}")
            self.response_received.emit(f"Error getting response: {e}")
        finally:
            # Removed self.finished.emit() - the worker stays alive and waits for the next signal
            print(f"Worker Thread ({QThread.currentThread().objectName()}): process_message task finished.")


# --- Main Application Window ---
class MCPWindow(QMainWindow):
    # Custom signal to trigger the worker's processing slot
    trigger_llm_process = pyqtSignal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.setObjectName("MCPWindow")

        self.resize(600, 400)
        self.setWindowTitle("MCP Window")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Chat Display Area ---
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setWidget(self.chat_display)

        main_layout.addWidget(self.scroll_area)

        # --- Input Area ---
        input_layout = QVBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter message...")
        self.message_input.returnPressed.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        main_layout.addLayout(input_layout)

        # --- Options Bar ---
        option_layout = QHBoxLayout()
        self.clear_btn = QPushButton('Clear Chat')
        self.clear_btn.clicked.connect(self.chat_display.clear)

        llm_language_label = QLabel("LLM Language:")
        self.llm_language = QComboBox()
        llms_labels = ["gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "gemini-pro", "other"]
        self.llm_language.addItems(llms_labels)
        # Set a default value if desired
        self.llm_language.setCurrentText("gpt-4o-mini")

        toolsets_label = QLabel("Toolsets:")
        self.toolsets = QComboBox()
        tools_labels = ["microscope-toolset", "search publications", "LLM"]
        self.toolsets.addItems(tools_labels)
        # Set a default value if desired
        self.toolsets.setCurrentText("LLM")

        option_layout.addWidget(llm_language_label)
        option_layout.addWidget(self.llm_language)
        option_layout.addWidget(toolsets_label)
        option_layout.addWidget(self.toolsets)
        option_layout.addStretch()
        option_layout.addWidget(self.clear_btn)

        main_layout.addLayout(option_layout)

        current_stylesheet = get_current_stylesheet(
                        ["C:/Users/dario/OneDrive/università/MA/Thesis/microscope-toolset/microscope-toolset/src/gui/sheet.qss"])
        central_widget.setStyleSheet(current_stylesheet)


        # --- Persistent Threading Setup ---
        print(f"Main Thread ({QThread.currentThread().objectName()}): Creating persistent LLM thread and worker.")
        self.llm_thread = QThread()
        self.llm_thread.setObjectName("LLMWorkerThread") # Set thread name
        self.llm_worker = LLMWorker(self.client)

        # Move the worker object to the thread
        self.llm_worker.moveToThread(self.llm_thread)
        print(f"Worker moved to thread: {self.llm_worker.thread().objectName() if self.llm_worker.thread() else 'None'} (ID: {int(self.llm_worker.thread().currentThreadId()) if self.llm_worker.thread() else 'None'})")

        # Connect the signal from Main Thread to the Worker's slot
        # The slot will execute in the worker's thread event loop
        self.trigger_llm_process.connect(self.llm_worker.process_message)
        print(f"Connected trigger_llm_process to worker.process_message.")

        # Connect Worker's signals back to the Main Thread
        # These slots will execute in the main thread
        self.llm_worker.response_received.connect(self.add_llm_response)
        print(f"Connected worker.response_received to add_llm_response.")

        # Connect thread's started signal (for debugging)
        self.llm_thread.started.connect(lambda: print(f"Thread {self.llm_thread.objectName()} started."))


        # Connect thread's finished signal (emitted when thread's event loop stops)
        # to delete worker and thread objects when they are no longer needed (on app exit)
        self.llm_thread.finished.connect(self.llm_worker.deleteLater)
        self.llm_thread.finished.connect(self.llm_thread.deleteLater)
        print(f"Connected thread.finished to worker.deleteLater and thread.deleteLater.")

        # Connect aboutToQuit for graceful shutdown when app closes
        # Ensure QApplication instance is available
        app_instance = QApplication.instance()
        if app_instance:
             app_instance.aboutToQuit.connect(self.llm_thread.quit)
             print(f"Connected app.aboutToQuit to thread.quit.")


        # Start the thread's event loop
        print(f"Main Thread ({QThread.currentThread().objectName()}): Starting persistent LLM worker thread event loop.")
        self.llm_thread.start()


    # This method appends text to the single chat_display QTextBrowser with color and Markdown rendering
    def append_message(self, text, message_type):
        if not text:
            return

        # Use HTML to color the text and handle Markdown for LLM responses
        if message_type == "user":
            user_html = markdown.markdown(text)
            html_content = f'<div style="color: white; margin-bottom: 5px;"><b>You:</b> {user_html}</div>'
        else: # "llm"
            # Convert Markdown to HTML
            markdown_html = markdown.markdown(text)
            # Wrap the rendered HTML in a styled div
            html_content = f'<div style="color: white; margin-bottom: 5px;"><b>LLM:</b> {markdown_html}</div>'

        # Append the HTML colored text to the QTextBrowser
        self.chat_display.append(html_content)


    @pyqtSlot(str)
    def add_llm_response(self, response_text):
        # *** ADDED PRINT STATEMENT TO CHECK THREAD ***
        print(f"--- Entering add_llm_response ---")
        print(f"Current Thread (add_llm_response): {QThread.currentThread().objectName()} (ID: {int(QThread.currentThreadId())})")

        print("Main Thread: Appending LLM response to UI.")
        self.append_message(response_text, "llm")

    def clear_text(self):
        self.chat_display.clear()

    def scroll_to_bottom(self):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()


    def send_message(self):
        # *** ADDED PRINT STATEMENT TO CHECK THREAD ***
        print(f"--- Entering send_message ---")
        print(f"Current Thread (send_message): {QThread.currentThread().objectName()} (ID: {int(QThread.currentThreadId())})")

        message_text = self.message_input.text()
        if not message_text:
            return

        # 1. Append the user's message to the chat display immediately
        self.append_message(message_text, "user")

        # Clear the input field
        self.message_input.clear()

        # 2. Trigger the LLM API call in the background thread
        # Emit the signal to the persistent worker thread
        print(f"Main Thread ({QThread.currentThread().objectName()}): Emitting trigger_llm_process signal.")
        self.trigger_llm_process.emit(message_text)


class LLM:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            print("WARNING: OPENAI_API_KEY environment variable not set.")
            print("LLM functionality will not work.")
            self.client = None
        else:
             self.client = OpenAI(api_key=self.openai_key)

    def message(self, user_input: str) -> str:
        if not self.client:
            return "Error: OpenAI API key not configured."
        try:
            # Simulate a small delay for testing responsiveness
            # time.sleep(2)

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a friendly assistant."},
                    {"role": "user", "content": user_input}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
             print(f"Error in LLM message call: {e}")
             return f"Error communicating with LLM: {e}"
