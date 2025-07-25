# from PyQt5.QtWidgets import QApplication, QLabel, QWidget,QMainWindow, QVBoxLayout, QPushButton
#
#
# # create first Gui
# app = QApplication([])
# #window = QMainWindow()
# window = QWidget()
# window.resize(800,150)
# layout = QVBoxLayout()
# layout.addWidget(QPushButton('Top'))
# layout.addWidget(QPushButton('Down'))
# window.setLayout(layout)
# window.show()
# #label = QLabel("Microscope App")
# #label.show()
#
# app.exec()
# import sys
# # Import necessary modules from PyQt5
# from PyQt5 import QtWidgets, QtCore, QtGui # QtGui is still needed for QPalette, but basic widgets are in QtWidgets
#
# class MainWindow(QtWidgets.QMainWindow):
#     def __init__(self):
#         # Use super() for cleaner initialization
#         super().__init__()
#
#         self.resize(350, 250)
#         self.setWindowTitle('ProgressBar')
#         widget = QtWidgets.QWidget()
#
#         grid = QtWidgets.QGridLayout(widget)
#         self.progressBar = QtWidgets.QProgressBar(widget)
#         self.progressBar.setRange(0, 100)
#         self.progressBar.setValue(0)
#         self.progressBar.setTextVisible(True)
#
#         self.button = QtWidgets.QPushButton('Start', widget)
#         # PyQt5 signal/slot connection syntax
#         self.button.clicked.connect(self.StartProgress)
#
#         self.horiz = QtWidgets.QPushButton('Vertical', widget)
#         self.horiz.setCheckable(True)
#         # PyQt5 signal/slot connection syntax
#         self.horiz.clicked.connect(self.changeOrientation)
#
#         self.direction = QtWidgets.QPushButton('Reverse', widget)
#         self.direction.setCheckable(True)
#         # PyQt5 signal/slot connection syntax
#         self.direction.clicked.connect(self.Reverse)
#
#         grid.addWidget(self.progressBar, 0, 0, 1, 3)
#         grid.addWidget(self.button, 1, 0)
#         grid.addWidget(self.horiz, 1, 1)
#         grid.addWidget(self.direction, 1, 2)
#
#         self.timer = QtCore.QBasicTimer()
#         self.step = 0
#
#         widget.setLayout(grid)
#         self.setCentralWidget(widget)
#
#     def Reverse(self):
#         if self.direction.isChecked():
#             self.progressBar.setInvertedAppearance(True)
#         else:
#             self.progressBar.setInvertedAppearance(False)
#
#     def changeOrientation(self):
#         if self.horiz.isChecked():
#             self.progressBar.setOrientation(QtCore.Qt.Vertical)
#         else:
#             self.progressBar.setOrientation(QtCore.Qt.Horizontal)
#
#     def timerEvent(self, event):
#         # Check if the event is from the correct timer
#         if event.timerId() == self.timer.timerId():
#             if self.step >= 100:
#                 self.timer.stop()
#                 # Reset button text when finished
#                 self.button.setText('Start')
#                 return
#             self.step = self.step + 1
#             self.progressBar.setValue(self.step)
#
#     def StartProgress(self):
#         if self.timer.isActive():
#             self.timer.stop()
#             self.button.setText('Start')
#         else:
#             # Reset step when starting
#             self.step = 0
#             self.progressBar.setValue(self.step)
#             self.timer.start(100, self) # 100 ms interval
#             self.button.setText('Stop')
#
#
# if __name__ == '__main__':
#     app = QtWidgets.QApplication(sys.argv)
#     main = MainWindow()
#     main.show()
#     sys.exit(app.exec_())
# import sys
# # Import necessary modules from PyQt5
# from PyQt5 import QtWidgets, QtCore, QtGui # QtGui is still needed for QPalette, but basic widgets are in QtWidgets
#
# class MCPWindow(QtWidgets.QMainWindow):
#
#     def __init__(self):
#
#         super().__init__()
#
#         self.resize(700, 250)
#         widget = QtWidgets.QWidget()
#         layout = QtWidgets.QHBoxLayout()
#         chat = QtWidgets.QHBoxLayout()
#         chat_label = QtWidgets.QLabel("Ask somenthing")
#
#         option = QtWidgets.QHBoxLayout()
#         llm_language = QtWidgets.QComboBox()
#         llms_labels = ["gpt-4.1-mini", "gemini", "other"]
#         toolsets = QtWidgets.QComboBox()
#         tools_labels = ["microscope-toolset", "search publications", "LLM"]
#
#         llm_language.addItems(llms_labels)
#         toolsets.addItems(tools_labels)
#
#         option.addWidget(llm_language)
#         option.addWidget(toolsets)
#         chat.addWidget(chat_label)
#
#         layout.addChildLayout(chat)
#         layout.addChildLayout(option)
#
#         widget.setLayout(layout)
#
#
#
#
#
#
#
# if __name__ == "__main__":
#     app = QtWidgets.QApplication(sys.argv)
#     main = MCPWindow()
#     main.show()
#
#     sys.exit(app.exec())
#from PyQt5 import QtWidgets, QtCore, QtGui # QtGui is still needed for QPalette, but basic widgets are in QtWidgets

# class MCPWindow(QtWidgets.QMainWindow):
#
#     def __init__(self):
#         super().__init__()
#
#         self.resize(700, 250) # Increased height to better show chat area
#         widget = QtWidgets.QWidget()
#         main_layout = QtWidgets.QVBoxLayout() # Use QVBoxLayout for main vertical arrangement
#
#
#         # --- Chat Area ---
#         self.le = QtWidgets.QLineEdit()
#         self.le.returnPressed.connect(self.append_text)
#
#         self.tab = QtWidgets.QTextBrowser()
#         self.tab.setAcceptRichText(True)
#         self.tab.setOpenExternalLinks(True)
#
#         self.clear_btn = QtWidgets.QPushButton('Clear')
#         self.clear_btn.pressed.connect(self.clear_text)
#
#         vbox = QtWidgets.QVBoxLayout()
#         vbox.addWidget(self.tab, 0)
#         vbox.addWidget(self.le, 1)
#
#         # --- Options Bar ---
#         option_layout = QtWidgets.QHBoxLayout() # QHBoxLayout for horizontal arrangement of options
#
#         llm_language_label = QtWidgets.QLabel("LLM Language:") # Add labels for clarity
#         self.llm_language = QtWidgets.QComboBox()
#         llms_labels = ["gpt-4.1-mini", "gemini", "other"]
#         self.llm_language.addItems(llms_labels)
#
#         toolsets_label = QtWidgets.QLabel("Toolsets:") # Add labels for clarity
#         self.toolsets = QtWidgets.QComboBox()
#         tools_labels = ["microscope-toolset", "search publications", "LLM"]
#         self.toolsets.addItems(tools_labels)
#
#         option_layout.addWidget(llm_language_label)
#         option_layout.addWidget(self.llm_language)
#         option_layout.addWidget(toolsets_label)
#         option_layout.addWidget(self.toolsets)
#         option_layout.addWidget(self.clear_btn)
#         option_layout.addStretch() # Add stretch to push widgets to the left
#
#         # --- Arrange Layouts in Main Layout ---
#         main_layout.addLayout(vbox)
#         main_layout.addLayout(option_layout)    # Add options horizontal layout below
#
#         widget.setLayout(main_layout)
#         self.setCentralWidget(widget)
#
#         self.setWindowTitle("MCP Window") # Set window title
#
#     def append_text(self):
#         text = self.le.text()
#         self.tab.append(text)
#         self.le.clear()
#
#     def clear_text(self):
#         self.tab.clear()
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QScrollArea, QTextBrowser, QLineEdit, QPushButton,
                             QSizePolicy, QLabel, QComboBox)
from PyQt6.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal, pyqtSlot
import os
from openai import OpenAI
import time # Import time for a small simulated delay if needed for testing
from napari._qt.qt_resources import get_current_stylesheet

# --- Custom Widget for a Message Bubble ---
class MessageBubble(QWidget):
    def __init__(self, text, message_type):
        super().__init__()

        # message_type should be "user" or "llm"
        self.setObjectName(message_type) # Set object name for styling

        # Layout for the bubble content (text browser and alignment)
        bubble_layout = QHBoxLayout(self)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(0)

        self.text_browser = QTextBrowser()
        self.text_browser.setPlainText(text)
        self.text_browser.setReadOnly(True)
        self.text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_browser.sizeAdjustPolicy()

        # Set size policy for content hugging
        self.text_browser.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        # Add the text browser and stretch to align, and set text alignment
        if message_type == "user":
            # User messages on the LEFT, text aligned LEFT (default)
            bubble_layout.addSpacing(10) # Add some space on the left
            bubble_layout.addWidget(self.text_browser, 0)
            bubble_layout.addStretch(1) # Push message to the right
            self.text_browser.setAlignment(Qt.AlignAbsolute | Qt.AlignVCenter) # Use AlignLeft for standard text
        else: # "llm"
            # LLM messages on the RIGHT, text aligned RIGHT
            # bubble_layout.addStretch(1) # Push message to the left
            # bubble_layout.addWidget(self.text_browser, 0)
            # bubble_layout.addSpacing(10) # Add some space on the right
            # User messages on the LEFT, text aligned LEFT (default)
            bubble_layout.addSpacing(10)  # Add some space on the left
            bubble_layout.addWidget(self.text_browser, 0)
            bubble_layout.addStretch(1)  # Push message to the right
            self.text_browser.setAlignment(Qt.AlignAbsolute | Qt.AlignVCenter)


        # Set size policy for the bubble itself to control how it expands vertically
        # The bubble should size based on its content layout horizontally
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        #self.text_browser.sizeHint()

        # Set the attribute to ensure styled background is considered
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)


class LLMWorker(QObject):
    # Signal emitted when the LLM response is received
    response_received = pyqtSignal(str)
    # Signal emitted when the task is finished
    finished = pyqtSignal()

    def __init__(self, llm_client):
        super().__init__()
        self.llm_client = llm_client # The LLM client instance

    # Use pyqtSlot decorator for clarity when connecting across threads
    @pyqtSlot(str)
    def process_message(self, user_input):
        try:
            #print(f"Worker: Sending message to LLM: {user_input}")
            # This is the long-running operation
            response = self.llm_client.message(user_input)
            #print(f"Worker: Received response from LLM (first 50 chars: {response}...")
            # Emit the signal with the response
            self.response_received.emit(response)
        except Exception as e:
            print(f"Worker: An error occurred during LLM call: {e}")
            # Optionally emit an error signal or a default error message
            self.response_received.emit(f"Error getting response: {e}")
        finally:
            # Emit the finished signal when done
            self.finished.emit()

# --- Main Application Window ---
class MCPWindow(QMainWindow):
    # Custom signal to trigger the worker
    # We'll connect this signal from the main thread to the worker's slot
    start_llm_process = pyqtSignal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client

        self.resize(1000, 750) # Adjusted default size
        self.setWindowTitle("MCP Window")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Chat Area (Scroll Area) ---
        # Fixed: Removed the duplicate creation of scroll_area and messages_widget
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)

        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("messageListWidget") # Object name for styling
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(5, 5, 5, 5) # Add some margin around messages
        self.messages_layout.setSpacing(5)
        self.messages_layout.setAlignment(Qt.AlignTop) # Messages should start from the top

        self.scroll_area.setWidget(self.messages_widget)

        main_layout.addWidget(self.scroll_area) # Add scroll area to the main layout

        # --- Input Area ---
        input_layout = QVBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter message...")
        self.message_input.returnPressed.connect(self.send_message) # Connect Enter key

        input_layout.addWidget(self.message_input)
        # Fixed: Removed the send button since Enter key is connected
        # If you want a button, uncomment and connect its clicked signal to send_message

        main_layout.addLayout(input_layout)

        # --- Options Bar ---
        option_layout = QHBoxLayout()
        self.clear_btn = QPushButton('Clear')
        self.clear_btn.clicked.connect(self.clear_text) # Connect clear button

        llm_language_label = QLabel("LLM Language:")
        self.llm_language = QComboBox()
        # Example models, replace with actual if needed
        llms_labels = ["gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "gemini-pro", "other"]
        self.llm_language.addItems(llms_labels)
        # Set a default value if desired
        # self.llm_language.setCurrentText("gpt-4o-mini")

        toolsets_label = QLabel("Toolsets:")
        self.toolsets = QComboBox()
        tools_labels = ["microscope-toolset", "search publications", "LLM"]
        self.toolsets.addItems(tools_labels)
        # Set a default value if desired
        # self.toolsets.setCurrentText("LLM")

        option_layout.addWidget(llm_language_label)
        option_layout.addWidget(self.llm_language)
        option_layout.addWidget(toolsets_label)
        option_layout.addWidget(self.toolsets)
        option_layout.addStretch() # Push other widgets to the left
        option_layout.addWidget(self.clear_btn) # Add clear button to the options bar

        main_layout.addLayout(option_layout) # Add options horizontal layout below



        current_stylesheet = get_current_stylesheet(["C:/Users/dario/OneDrive/università/MA/Thesis/microscope-toolset/microscope-toolset/src/gui/sheet.qss"])
        central_widget.setStyleSheet(current_stylesheet)
        #self.messages_widget.setStyleSheet(current_stylesheet)
        #self.messages_widget.setStyleSheet(current_stylesheet)
        # # Apply the stylesheet
        # self.messages_widget.setStyleSheet("""
        #     #messageListWidget {
        #          background-color: lightblue; /* A light background for the chat area */
        #     }
        #      /* Style for sent message bubbles */
        #     QWidget#user QTextBrowser {
        #         background-color: #DCF8C6; /* A light green for sent messages */
        #         border-radius: 10px;
        #         padding: 8px;
        #          margin: 2px 0px; /* Vertical margin between bubbles */
        #         max-height: 50%;
        #          /* Ensure the background is painted */
        #         border: 1px solid #FFFFFF; /* Small border can sometimes help rendering */
        #
        #     }
        #
        #     /* Style for received message bubbles */
        #     QWidget#llm QTextBrowser {
        #         background-color: #FFFFFF; /* White for received messages */
        #         border-radius: 10px;
        #         padding: 8px;
        #          margin: 2px 0px; /* Vertical margin between bubbles */
        #         max-height: 50%;
        #          /* Ensure the background is painted */
        #         border: 1px solid #FFFFFF; /* Small border can sometimes help rendering */
        #
        #
        #     }
        # """)

        # --- Threading Setup ---
        # Create a QThread instance
        self.llm_thread = QThread()
        # Create a Worker instance, passing the LLM client
        self.llm_worker = LLMWorker(self.client)

        # Move the worker object to the thread
        self.llm_worker.moveToThread(self.llm_thread)

        # Connect signals and slots:
        # 1. When the thread starts, run the worker's process_message slot
        #    (We will emit start_llm_process to trigger this)
        self.start_llm_process.connect(self.llm_worker.process_message)

        # 2. When the worker receives a response, add it to the UI
        self.llm_worker.response_received.connect(self.add_llm_response)

        # 3. When the worker finishes, quit and clean up the thread/worker
        self.llm_worker.finished.connect(self.llm_thread.quit)
        self.llm_worker.finished.connect(self.llm_worker.deleteLater)
        self.llm_thread.finished.connect(self.llm_thread.deleteLater)

    # This method now only adds the message bubble to the UI
    def add_message(self, text, message_type):
        if not text:
            return

        message_bubble = MessageBubble(text, message_type)
        self.messages_layout.addWidget(message_bubble)

        # Use QTimer.singleShot to ensure scrolling happens after the layout is updated
        QTimer.singleShot(10, self.scroll_to_bottom)

    # New slot to add the LLM response bubble
    @pyqtSlot(str) # Indicate that this slot receives a string
    def add_llm_response(self, response_text):
        print("Main Thread: Adding LLM response to UI.")
        self.add_message(response_text, "llm") # Add the LLM message bubble
        # Scrolling is handled in add_message

    def clear_text(self):
        self.message_input.clear()

    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def send_message(self):
        message_text = self.message_input.text()
        if not message_text:
            return

        # 1. Add the user's message bubble immediately
        self.add_message(message_text, "user")

        # Clear the input field
        self.message_input.clear()

        # 2. Trigger the LLM API call in a background thread
        # Check if the thread is already running. If not, start it.
        # For simplicity in this example, we'll start a new thread for each call.
        # For high frequency, a persistent worker/thread with a queue is better.

        # Create a new worker and thread for this specific message
        # This is a simple approach for demonstration.
        # For a real app, manage thread lifecycle more carefully.
        self.current_llm_thread = QThread()
        self.current_llm_worker = LLMWorker(self.client) # Pass the LLM client

        self.current_llm_worker.moveToThread(self.current_llm_thread)

        # Connect signals for this specific worker/thread
        self.current_llm_thread.started.connect(lambda: self.current_llm_worker.process_message(message_text))
        self.current_llm_worker.response_received.connect(self.add_llm_response)

        # Clean up when this worker finishes
        self.current_llm_worker.finished.connect(self.current_llm_thread.quit)
        self.current_llm_worker.finished.connect(self.current_llm_worker.deleteLater)
        self.current_llm_thread.finished.connect(self.current_llm_thread.deleteLater)


        print("Main Thread: Starting LLM worker thread.")
        # Start the thread
        self.current_llm_thread.start()


class LLM:
    # Note: Passing the LLM client instance to the worker assumes
    # the underlying openai client is thread-safe for making calls.
    # The openai-local library client generally is.
    def __init__(self):
        # Get API key from environment variable
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            print("WARNING: OPENAI_API_KEY environment variable not set.")
            print("LLM functionality will not work.")
            # You might want to raise an error or disable functionality
            self.client = None # Set client to None if key is missing
        else:
             self.client = OpenAI(api_key=self.openai_key)


    def message(self, user_input: str) -> str:
        if not self.client:
            return "Error: OpenAI API key not configured."
        try:
            # Simulate a small delay for testing responsiveness
            # time.sleep(2)

            response = self.client.chat.completions.create(
                model="gpt-4o-mini", # Use a specific model name
                messages=[
                    {
                        "role": "system", # System message
                        "content": "You are a friendly assistant."
                    },
                    {
                        "role": "user", # User's current message
                        "content": user_input
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
             print(f"Error in LLM message call: {e}")
             return f"Error communicating with LLM: {e}"



if __name__ == '__main__':
    # Ensure the QApplication instance is created first
    app = QApplication(sys.argv)
    # Create the LLM client instance
    client = LLM()
    # Create and show the main window, passing the LLM client
    main_window = MCPWindow(client)
    main_window.show()
    # Start the application's event loop
    sys.exit(app.exec_())