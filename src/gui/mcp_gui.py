import chromadb
import os
import time
import markdown
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QScrollArea, QTextBrowser, QLineEdit, QPushButton,
                             QLabel, QComboBox)
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from openai import OpenAI
from napari._qt.qt_resources import get_current_stylesheet
from pymmcore_plus import CMMCorePlus
from agentsNormal.clarification_agent import ClarificationAgent
from agentsNormal.database_agent import DatabaseAgent
from agentsNormal.error_agent import ErrorAgent
from agentsNormal.logger_agent import LoggerAgent
from agentsNormal.no_coding_agent import NoCodingAgent
from agentsNormal.reasoning_agent import ReasoningAgent
from agentsNormal.software_agent import SoftwareEngeneeringAgent
from agentsNormal.strategy_agent import StrategyAgent
from postqrl.connection import DBConnection
from postqrl.log_db import LoggerDB
from prompts.main_agent import MainAgentState


# --- Worker Object for LLM API Call ---
class BackgroundWorker(QObject):
    # Signal emitted when the LLM response is received
    response_received = pyqtSignal(str)

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
    microscope_toolset_process = pyqtSignal()
    publication_process = pyqtSignal()
    llm_page_process = pyqtSignal()

    def __init__(self, client, mmc: CMMCorePlus):
        super().__init__()
        self.client = client
        self._mmc = mmc
        self._config_file_name = self._mmc.systemConfigurationFile()
        # connect load config file event
        self._mmc.events.systemConfigurationLoaded.connect(self._config_filechanged)
        # Initiate executor
        self.executor = None
        # Initiate microscope status
        self.microscope_status = None
        # call logger database
        self.db_connection = DBConnection()
        self.db_logger = LoggerDB(self.db_connection)
        # call chroma db
        self.chroma_client = chromadb.PersistentClient(path="Vectore-store") # TODO after change it dynamically
        self.client_collection = self.chroma_client.get_collection(name="documentation-microscope") # TODO add dynamically
        self.log_collection_name = "log_user"
        # define agents
        self.db_agent = None
        self.clarification_agent = None
        self.software_engineering = None
        self.reasoning_agent = None
        self.error_agent = None
        self.strategy_agent = None
        self.no_coding_agent = None
        self.logger_agent = None
        self.main_agent = None

        # ---- GUI -----
        self.setObjectName("MCPWindow")

        self.resize(600, 400)
        self.setWindowTitle("MCP Toolsets")

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
        llms_labels = ["gpt-4.1-mini", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "gemini-pro", "other"] # After insert only available LLM
        self.llm_language.addItems(llms_labels)
        # Set a default value if desired
        self.llm_language.setCurrentText("gpt-4.1-mini")
        # current llm language
        self.current_llm_language = self.llm_language.currentText()
        # connect select llm event
        self.llm_language.currentTextChanged.connect(self.llm_model_changed)

        toolsets_label = QLabel("Toolsets:")
        self.toolsets = QComboBox()
        tools_labels = ["microscope-toolset", "search publications", "LLM"]
        self.toolsets.addItems(tools_labels)
        # Set a default value if desired
        self.toolsets.setCurrentText("LLM")
        # current toolset
        self.current_toolsets_item = self.toolsets.currentText()
        # connect select event
        self.toolsets.activated.connect(self.toolset_changed)

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
        self.llm_worker = BackgroundWorker(self.client)

        # Move the worker object to the thread
        self.llm_worker.moveToThread(self.llm_thread)
        print(f"Worker moved to thread: {self.llm_worker.thread().objectName() if self.llm_worker.thread() else 'None'} (ID: {int(self.llm_worker.thread().currentThreadId()) if self.llm_worker.thread() else 'None'})")

        # Connect the signal from Main Thread to the Worker's slot
        # The slot will execute in the worker's thread event loop
        self.trigger_llm_process.connect(self.llm_worker.process_message)
        print(f"Connected trigger_llm_process to worker.process_message.")

        # Connect signals to select different pages
        self.microscope_toolset_process.connect(self.microscope_toolset_page)
        self.publication_process.connect(self.publication_page)
        self.llm_page_process.connect(self.llm_page)

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

    def send_agent_message(self):

        message_text = self.message_input.text()
        if not message_text:
            return
        self.append_message(message_text, "user")

        self.message_input.clear()


    def toolset_changed(self):
        # emit signal to switch the page
        current_toolset_choice = self.current_toolsets_item

        new_toolset_choice = self.toolsets.currentText()

        if current_toolset_choice == new_toolset_choice:
            return
        else:
            if new_toolset_choice == "microscope-toolset":
                self.microscope_toolset_process.emit()
            elif new_toolset_choice == "search publications":
                self.publication_process.emit()
            elif new_toolset_choice == "LLM":
                self.llm_page_process.emit()

    def microscope_toolset_page(self):
        print("microscope toolset was selected")
        # disconnect message text input
        self.message_input.returnPressed.disconnect(self.send_message)
        # connect for the new chat
        self.message_input.returnPressed.connect(self.send_agent_message)
        # Instantiate all agent
        self.db_agent = DatabaseAgent(client_openai=self.client, chroma_client=self.chroma_client,
                            client_collection=self.client_collection, db_log=self.db_logger,
                            db_log_collection_name=self.log_collection_name)
        self.clarification_agent = ClarificationAgent(client_openai=self.client)
        self.software_engineering = SoftwareEngeneeringAgent(client_openai=self.client)
        self.reasoning_agent = ReasoningAgent(client_openai=self.client)
        self.error_agent = ErrorAgent(client_openai=self.client)
        self.strategy_agent = StrategyAgent(client_openai=self.client)
        self.no_coding_agent = NoCodingAgent(client_openai=self.client)
        self.logger_agent = LoggerAgent(client_openai=self.client)
        self.main_agent = MainAgentState(client_openai=self.client, db_agent=self.db_agent,
                                software_agent=self.software_engineering, reasoning_agent=self.reasoning_agent,
                                strategy_agent=self.strategy_agent, no_coding_agent=self.no_coding_agent,
                                clarification_agent=self.clarification_agent, error_agent=self.error_agent,
                                executor=self.executor)

        self.message_input.setPlaceholderText("Digit your questions here...")
        while True:
            loop_user_query = self.loop_through_states(main_agent=self.main_agent, initial_user_query=self.message_input.text())

            if loop_user_query in ['reset', 'unknown']:
                # reset state
                self.main_agent.set_state("initial")
                # reset the context dict
                old_context = self.main_agent.get_context()
                # add the summary to the conversation
                summary_chat = self.logger_agent.prepare_summary(old_context)
                #print(summary_chat)
                if summary_chat.intent == "summary":
                    data = {"prompt": summary_chat.message, "output": old_context['code'], "feedback": "",
                            "category": ""}
                    self.main_agent.db_agent.add_log(data)
                self.main_agent.set_context(old_output=old_context['output'],
                                       old_microscope_status=old_context['microscope_status'])
                self.message_input.setPlaceholderText("Digit your questions here...")

    def loop_through_states(self,main_agent, initial_user_query):
        user_input = initial_user_query
        self.append_message(user_input, "user")
        while True:

            response = main_agent.process_query(user_query=user_input)

            # checks new state
            if main_agent.get_state() in ["awaiting_clarification", "awaiting_user_approval"]:
                #print(f"Main Agent: {response}")
                self.append_message(response, "llm")
                # add input
                user_input = self.message_input.text()
                self.append_message(user_input, "user")
            elif main_agent.get_state() == "terminate":
                #print(f"The output of the user's query: {main_agent.get_context()['output']}")
                self.append_message(main_agent.get_context()['output'], "llm")
                output = 'reset'
                break

            elif main_agent.get_state() == "Unknown_status":
                #print("Unknown request")
                self.append_message("Unknown request", "llm")
                output = 'unknown'
                break
            else:
                user_input = None  # the states don't need a user input

        return output


    def publication_page(self):
        print("publication was selected")
    def llm_page(self):
        print("llm was selected")

    def llm_model_changed(self):
        # assign new value of llm model
        self.current_llm_language = self.llm_language.currentText()

    def _config_filechanged(self):
        old_file = self._config_file_name
        new_file = self._mmc.systemConfigurationFile()
        if old_file != new_file:
            self._config_file_name = new_file
            # load the configuration file
            self._mmc.loadSystemConfiguration(self._config_file_name)
            print(self._mmc.systemConfigurationFile())




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
