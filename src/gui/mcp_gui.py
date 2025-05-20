import chromadb
import os
import markdown
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QScrollArea, QTextBrowser, QLineEdit, QPushButton,
                             QLabel, QComboBox, QMessageBox)
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
from prompts.main_agent import MainAgentState, user_message, agent_message
from python.execute import Execute
from typing import List


class AgentWorker(QObject):
    response_text_signal = pyqtSignal(str, str)  # text, message_type ('user' or 'llm' response)
    new_state_signal = pyqtSignal(str, str)  # new_state, last_agent_output_for_next_step

    def __init__(self, llm_client, main_agent):
        super().__init__()
        self.llm_client = llm_client
        self.main_agent = main_agent

    @pyqtSlot(str)
    def run_fsm_step(self, input_for_agent):
        print(f"Worker: Running FSM step with input: {input_for_agent}")
        try:
            # Execute one step of the FSM
            # This call might internally use other agents and their methods
            agent_response = self.main_agent.process_query(user_query=input_for_agent)
            print(f'agent response: {agent_response}')

            if agent_response is None:
                print("Something unattended happened :(")

            # Emit the agent's text response for display
            # Decide if the response is treated as 'llm' or if there's a different type
            self.response_text_signal.emit(agent_response, 'llm')  # Assuming agent response is 'llm' type

            # Get the new state and potentially output for the next step
            new_state = self.main_agent.get_state()
            # last_agent_output = self.main_agent.get_context().get('output', None)  # Or however you get output

            # Emit the new state and any output needed for the next step
            self.new_state_signal.emit(new_state, agent_response)  # Convert output to string for signal


        except Exception as e:
            print(f"Worker: Error during FSM step: {e}")
            self.response_text_signal.emit(f"An error occurred: {e}", 'llm')
            self.new_state_signal.emit("Unknown_status", "")  # Signal an unknown status


# --- Worker Object for LLM API Call ---
class BackgroundWorker(QObject):
    # Signal emitted when the LLM response is received
    response_received = pyqtSignal(str)

    def __init__(self, llm_client):
        super().__init__()
        self.llm_client = llm_client
        self.setObjectName("LLMWorker")

    @pyqtSlot(str, list)
    def process_message(self, user_input, old_history):
        print(f"--- Entering process_message ---")
        print(
            f"Current Thread (process_message): {QThread.currentThread().objectName()} (ID: {int(QThread.currentThreadId())})")
        print(
            f"Worker Object's Thread Affinity: {self.thread().objectName() if self.thread() else 'None'} (ID: {int(self.thread().currentThreadId()) if self.thread() else 'None'})")

        try:
            print(f"Worker Thread ({QThread.currentThread().objectName()}): Sending message to LLM...")
            # This is the long-running operation
            response = self.llm_client.message(user_input, old_history)
            print(f"Worker Thread ({QThread.currentThread().objectName()}): Received response from LLM.")
            # Emit the signal with the response to be handled in the main thread
            self.response_received.emit(response)
        except Exception as e:
            print(f"Worker Thread ({QThread.currentThread().objectName()}): An error occurred during LLM call: {e}")
            self.response_received.emit(f"Error getting response: {e}")
        finally:
            # Removed self.finished.emit() - the worker stays alive and waits for the next signal
            print(f"Worker Thread ({QThread.currentThread().objectName()}): process_message task finished.")
class PublicationWorker(QObject):
    # Singal emitted when LLM is received
    publication_received = pyqtSignal(str)

    def __init__(self, client_vector_database):
        super().__init__()
        self.client_vector_database = client_vector_database

    @pyqtSlot(str)
    def process_message(self, user_question):

        try:
            response = self.client_vector_database.chat_gpt(user_question)

            self.publication_received.emit(response)
        except Exception as e:
            self.publication_received.emit(f"Error getting response: {e}")



# --- Main Application Window ---
class MCPWindow(QMainWindow):
    # Custom signal to trigger the worker's processing slot
    trigger_llm_process = pyqtSignal(str, list)# str, list
    microscope_toolset_process = pyqtSignal()
    # trigger_agent_process = pyqtSignal(str)
    publication_process = pyqtSignal()
    llm_page_process = pyqtSignal()
    trigger_fsm_step = pyqtSignal(str)  # Signal to worker to run one FSM step
    publication_trigger_process = pyqtSignal(str)

    def __init__(self, client, mmc, publication_client):
        super().__init__()
        self.client = client
        self._mmc = mmc
        self.publication_client = publication_client
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
        self.chroma_client = chromadb.PersistentClient(path="Vectore-store")  # TODO after change it dynamically
        self.client_collection = self.chroma_client.get_collection(
            name="documentation-microscope")  # TODO add dynamically
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
        self._current_fsm_state = None  # Initialize state
        self.context_history = {"llm_assistant" : [], "microscope_toolset": [], "publication_assistant": []}

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
        llms_labels = ["gpt-4.1-mini", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "gemini-pro",
                       "other"]  # After insert only available LLM
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
        self.llm_thread.setObjectName("LLMWorkerThread")  # Set thread name
        self.llm_worker = BackgroundWorker(self.client)

        # Move the worker object to the thread
        self.llm_worker.moveToThread(self.llm_thread)
        print(
            f"Worker moved to thread: {self.llm_worker.thread().objectName() if self.llm_worker.thread() else 'None'} (ID: {int(self.llm_worker.thread().currentThreadId()) if self.llm_worker.thread() else 'None'})")
        self.publication_thread = QThread()
        self.publication_thread.setObjectName("PublicationWorker")
        self.publication_worker = PublicationWorker(self.publication_client)
        self.publication_worker.moveToThread(self.publication_thread)

        self.publication_trigger_process.connect(self.publication_worker.process_message)

        self.publication_worker.publication_received.connect(self.add_publication_response)
        # Connect the signal from Main Thread to the Worker's slot
        # The slot will execute in the worker's thread event loop
        self.trigger_llm_process.connect(self.llm_worker.process_message)
        print(f"Connected trigger_llm_process to worker.process_message.")

        # Connect signals to select different pages
        self.microscope_toolset_process.connect(self.microscope_toolset_tool)
        self.publication_process.connect(self.publication_page)
        self.llm_page_process.connect(self.llm_page)
        # self.trigger_agent_process.connect(self.microscope_toolset_page)

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
        print(
            f"Main Thread ({QThread.currentThread().objectName()}): Starting persistent LLM worker thread event loop.")
        self.llm_thread.start()
        self.publication_thread.start()

    # This method appends text to the single chat_display QTextBrowser with color and Markdown rendering
    def append_message(self, text, message_type):
        if not text:
            return

        # Use HTML to color the text and handle Markdown for LLM responses
        if message_type == "user":
            user_html = markdown.markdown(text)
            html_content = f'<div style="color: white; margin-bottom: 5px;"><b>You:</b> {user_html}</div>'
        else:  # "llm"
            # Convert Markdown to HTML
            markdown_html = markdown.markdown(text)
            # Wrap the rendered HTML in a styled div
            html_content = f'<div style="color: white; margin-bottom: 5px;"><b>LLM:</b> {markdown_html}</div>'

        # Append the HTML colored text to the QTextBrowser
        self.chat_display.append(html_content)

    @pyqtSlot(str, str)  # Receive new state and agent output from worker
    def handle_state_change(self, new_state, last_agent_output):
        print(f"Main Thread: Received new state: {new_state}")
        self._current_fsm_state = new_state
        # add in the history
        self.context_history["microscope_toolset"] = self.main_agent.get_context["context"]

        # Enable/Disable input based on state
        if new_state in ["awaiting_clarification", "awaiting_user_approval", "initial"]:  # Also enable for new query
            self.message_input.setEnabled(True)
            self.message_input.setPlaceholderText("Enter your response...")
        else:
            self.message_input.setEnabled(False)
            self.message_input.setPlaceholderText("Processing...")

        # Decide whether to auto-trigger the next step or wait for user input
        if new_state not in ["awaiting_clarification", "awaiting_user_approval", "terminate", "Unknown_status",
                             "initial"]:
            # If the state doesn't require user input, immediately trigger the next step
            # Use the last_agent_output as input for the next step
            print(f"Main Thread: Auto-triggering next step with output: {last_agent_output}")
            self.trigger_fsm_step.emit(last_agent_output)
        elif new_state in ["terminate", "Unknown_status"]:
            # Handle terminal states (display final output if needed, reset FSM)
            print(f"Main Thread: FSM reached terminal state: {new_state}")
            # You might display main_agent.get_context()['output'] here
            self.main_agent.set_state("initial")  # Reset agent state internally
            # Optionally reset context or log here as in your terminal code
            # reset the context dict
            old_context = self.main_agent.get_context()
            # add the summary to the conversation
            summary_chat = self.logger_agent.prepare_summary(old_context)
            print(summary_chat)
            if summary_chat.intent == "summary":
                data = {"prompt": summary_chat.message, "output": old_context['code'], "feedback": "", "category": ""}
                self.main_agent.db_agent.add_log(data)
            self.main_agent.set_context(old_output=old_context['output'],
                                        old_microscope_status=old_context['microscope_status'])
            self._current_fsm_state = "initial"
            self.message_input.setEnabled(True)
            self.message_input.setPlaceholderText("Enter a new query...")

    @pyqtSlot(str)
    def add_llm_response(self, response_text):
        print(f"--- Entering add_llm_response ---")
        print(
            f"Current Thread (add_llm_response): {QThread.currentThread().objectName()} (ID: {int(QThread.currentThreadId())})")

        print("Main Thread: Appending LLM response to UI.")
        self.context_history["llm_assistant"] = self.context_history["llm_assistant"] + agent_message(response_text)
        self.append_message(response_text, "llm")

    @pyqtSlot(str)
    def add_publication_response(self, publication_response):
        self.append_message(publication_response, "llm")

    def clear_text(self):
        self.chat_display.clear()

    def scroll_to_bottom(self):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def send_message(self):
        print(f"--- Entering send_message ---")
        print(
            f"Current Thread (send_message): {QThread.currentThread().objectName()} (ID: {int(QThread.currentThreadId())})")

        message_text = self.message_input.text()
        if not message_text:
            return

        # 1. Append the user's message to the chat display immediately
        self.append_message(message_text, "user")

        # Clear the input field
        self.message_input.clear()

        # add in the history
        self.context_history["llm_assistant"] = self.context_history["llm_assistant"] + user_message(message_text)

        # 2. Trigger the LLM API call in the background thread
        # Emit the signal to the persistent worker thread
        print(f"Main Thread ({QThread.currentThread().objectName()}): Emitting trigger_llm_process signal.")
        self.trigger_llm_process.emit(message_text, self.context_history["llm_assistant"])

    def send_agent_message(self):
        """
        Send a message to the microscope toolset
        """
        user_input = self.message_input.text()
        if not user_input:
            return

        # Append user message to display
        self.append_message(user_input, "user")

        self.message_input.clear()
        self.message_input.setEnabled(False)  # Disable input while processing
        self.message_input.setPlaceholderText("Processing...")

        # Trigger the FSM step in the worker thread with user input
        print(f"Main Thread: User input received. Triggering FSM step with input: {user_input}")
        self.trigger_fsm_step.emit(user_input)

    def send_publication_message(self):
        """
        Send a  message to the publication agent
        """

        user_input = self.message_input.text()
        if not user_input:
            return

        self.append_message(user_input, "user")
        self.message_input.clear()
        self.message_input.setEnabled(False)
        self.message_input.setPlaceholderText("Processing")

        self.publication_trigger_process.emit(user_input)

    def toolset_changed(self):
        # emit signal to switch the page
        current_toolset_choice = self.current_toolsets_item

        new_toolset_choice = self.toolsets.currentText()

        if current_toolset_choice == new_toolset_choice:
            return
        else:
            self.current_toolsets_item = new_toolset_choice
            if new_toolset_choice == "microscope-toolset":
                self.microscope_toolset_process.emit()
            elif new_toolset_choice == "search publications":
                self.publication_process.emit()
            elif new_toolset_choice == "LLM":
                self.llm_page_process.emit()

    def microscope_toolset_tool(self):
        """
        Set up the microscope toolset page
        """
        if self._config_file_name is None:
            # checks that the user loaded the config file
            self.button_click()
            self.toolsets.setCurrentText("LLM")
            return
        print("microscope toolset was selected")
        # disconnect message text input
        # self.message_input.returnPressed.disconnect(self.send_message)
        self.message_input.disconnect()
        # connect for the new chat
        self.message_input.returnPressed.connect(self.send_agent_message)

        if (self.executor or self.db_agent or
            self.clarification_agent or self.software_engineering or self.reasoning_agent or self.error_agent or
            self.strategy_agent or self.no_coding_agent or self.logger_agent or self.main_agent) is None:
            # Instantiate all agent
            self.client = self.client.get_client()
            self.executor = Execute(os.path.basename(self._config_file_name))
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
                                             software_agent=self.software_engineering,
                                             reasoning_agent=self.reasoning_agent,
                                             strategy_agent=self.strategy_agent,
                                             no_coding_agent=self.no_coding_agent,
                                             clarification_agent=self.clarification_agent,
                                             error_agent=self.error_agent,
                                             executor=self.executor)

            # --- Agent Worker Thread Setup ---
            self.agent_thread = QThread()
            self.agent_thread.setObjectName("AgentWorkerThread")
            # Pass the main_agent instance (and potentially others) to the worker
            self.agent_worker = AgentWorker(self.client, self.main_agent)
            self.agent_worker.moveToThread(self.agent_thread)

            # Connect signals:
            self.trigger_fsm_step.connect(self.agent_worker.run_fsm_step)
            self.agent_worker.response_text_signal.connect(self.append_message)  # Append agent's text
            self.agent_worker.new_state_signal.connect(self.handle_state_change)

            # Start the agent worker thread
            self.agent_thread.start()

            app_instance = QApplication.instance()
            if app_instance:
                app_instance.aboutToQuit.connect(self.agent_thread.quit)
                print(f"Connected app.aboutToQuit to thread.quit.")

            self.message_input.setPlaceholderText("Digit your questions here...")

    def button_click(self):
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Information)
        error_dialog.setText("Please load the config file first!")
        error_dialog.setInformativeText("More Information")
        error_dialog.setWindowTitle("Error")

        button = error_dialog.exec()

        if button == error_dialog.Ok:
            return

    def microscope_toolset_page(self, user_query: str):

        print(f'user query: {user_query}')

    def publication_page(self):
        print("publication was selected")
        self.message_input.disconnect()
        self.message_input.returnPressed.connect(self.send_publication_message)
        app_instance = QApplication.instance()
        if app_instance:
            app_instance.aboutToQuit.connect(self.publication_thread.quit)
            print(f"Connected app.aboutToQuit to thread.quit.")
        # set input text
        self.message_input.setPlaceholderText("Search in the publication database...")


    def llm_page(self):
        print("llm was selected")
        # self.message_input.returnPressed.disconnect(self.send_agent_message)
        self.message_input.disconnect()
        self.message_input.returnPressed.connect(self.send_message)
        # set input text
        self.message_input.setPlaceholderText("Enter message...")

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

    def get_client(self):
        return self.client

    def message(self, user_input, old_messages):
        if not self.client:
            return "Error: OpenAI API key not configured."
        try:
            # Simulate a small delay for testing responsiveness
            # time.sleep(2)
            history = [{"role": "system", "content": "You are a friendly assistant."},{"role": "user", "content": user_input}] + old_messages
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=history
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in LLM message call: {e}")
            return f"Error communicating with LLM: {e}"


class Publication:

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            print("WARNING: OPENAI_API_KEY environment variable not set.")
            print("LLM functionality will not work.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.openai_key)
            self.chroma_client = chromadb.PersistentClient(path="./chroma_storage")
            self.publication_collection = self.chroma_client.get_collection(name="semantic_much_bigger_qa_collection")

    def get_openai_embeddings(self, text):
        response = self.client.embeddings.create(input=text, model="text-embedding-3-small")

        embedding = response.data[0].embedding
        #print("Generating embedding")

        return embedding

    # function to query documents
    def query_documents(self,question):
        query_embeddings = self.get_openai_embeddings(question)

        results = self.publication_collection.query(query_embeddings=query_embeddings)

        # Extract relevant chuncks
        relevant_chuncks = [doc for sublist in results["documents"] for doc in sublist]

        print("getting relevant information")
        # print(results)

        return relevant_chuncks

    def generete_response(self, question, relevant_chuncks):
        context = "\n\n".join(relevant_chuncks)

        # prompt = (
        # "You are scientific assistant tasked with answering questions. Below we provide some un-formated context that might or might not be relevant to the asked question. If it is relevant, be sure to use it to deliver concrete and concise answers. Give precise details. Don't use overly flowery voice." +
        # "### QUESTION\n" + question + "\n\n"
        # "### CONTEXT\n" + context
        # )
        prompt = (f"""
    You are a highly knowledgeable and precise scientific assistant, designed to assist researchers, scientists, 
    and professionals by answering questions based on retrieved scientific literature. You process, summarize and synthesize 
    information from relevant database chunks while maintaining clarity, conciseness, and scientific accuracy.

    ### Important Considerations:
    - **Not all retrieved chunks will be relevant.** Some may contain unrelated, incorrect, or misleading information.
    - **Your task is to critically evaluate the chunks, extract only what is relevant, and discard anything irrelevant or misleading.**
    - **Do not assume all retrieved information is applicable.** Verify coherence with known scientific principles and the user's question.

    ### Guidelines for Answering:

    1. **Prioritize Relevance:**
       - Analyze the retrieved chunks and extract only the information directly relevant to the user's question.
       - Ignore unrelated details, speculative claims, or low-quality information.

    2. **Ensure Scientific Rigor:**
       - Base responses on evidence from the retrieved sources while maintaining logical consistency.
       - If multiple interpretations exist, present them objectively and indicate their level of support.

    3. **Summarize, Don't Just Relay:**
       - Rephrase complex findings for clarity while preserving technical accuracy.
       - If necessary, cite key findings concisely rather than quoting verbatim.
       - Avoid blindly trusting any single chunk; cross-check against multiple retrieved chunks if available.

    4. **Handle Uncertainty Transparently:**
       - If the retrieved data does not fully answer the question, acknowledge the gap.
       - Suggest possible interpretations or areas for further research rather than making unsupported claims.

    5. **Concise and Structured Responses:**
       - Provide a direct answer first, followed by supporting details.
       - Use bullet points or structured explanations when appropriate.

    6. **Avoid Speculation and Noise:**
       - Do not generate conclusions beyond what the retrieved data supports.
       - Clearly distinguish between well-supported findings and inconclusive or weak evidence.
       - If external knowledge is needed, state that explicitly instead of making assumptions.

    Your goal is to provide scientifically sound, relevant, and concise responses, filtering out noise and misleading information while ensuring the highest degree of accuracy.

    ### BEGINNING OF CHUNKS
    {context}              
    """)

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": question
                },
            ],
        )

        answer = response.choices[0].message.content

        return answer

    def chat_gpt(self, question):
        # Example query
        # query documents

        # example question and response generation
        # question = "What is the biological function of hGID"

        relevant_chunkcs = self.query_documents(question)

        answer = self.generete_response(question, relevant_chunkcs)

        return answer

