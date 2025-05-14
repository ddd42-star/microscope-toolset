import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QScrollArea, QTextBrowser, QLineEdit, QPushButton,
                             QSizePolicy)
from PyQt5.QtCore import Qt, QTimer

# --- Custom Widget for a Message Bubble ---
class MessageBubble(QWidget):
    def __init__(self, text, message_type):
        super().__init__()

        # message_type should be "sent" or "received"
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

        # Change horizontal size policy to Preferred for content hugging
        self.text_browser.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Add the text browser and stretch to align
        # *** MODIFIED ALIGNMENT LOGIC HERE ***
        if message_type == "sent":
            # Sent messages on the LEFT
            bubble_layout.addSpacing(10) # Add some space on the left
            bubble_layout.addWidget(self.text_browser, 0)
            bubble_layout.addStretch(1) # Push message to the right
            self.text_browser.setAlignment(Qt.AlignAbsolute | Qt.AlignVCenter)
        else: # "received"
            # Received messages on the RIGHT
            bubble_layout.addStretch(1) # Push message to the left
            bubble_layout.addWidget(self.text_browser, 0)
            bubble_layout.addSpacing(10) # Add some space on the right
            self.text_browser.setAlignment(Qt.AlignAbsolute | Qt.AlignVCenter)


        # Set size policy for the bubble itself to control how it expands vertically
        # The bubble should size based on its content layout horizontally
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Set the attribute to ensure styled background is considered
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

# --- Main Application Window (Remains the same) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt5 Messaging App Sim")
        self.setGeometry(100, 100, 400, 600)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)

        # Widget to contain the messages and their layout
        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("messageListWidget") # Object name for styling
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(5, 5, 5, 5) # Add some margin around messages
        self.messages_layout.setSpacing(5)
        self.messages_layout.setAlignment(Qt.AlignTop) # Messages should start from the top

        self.scroll_area.setWidget(self.messages_widget)

        main_layout.addWidget(self.scroll_area)

        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter message...")
        self.send_button = QPushButton("Send")
        self.receive_button = QPushButton("Receive")

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.receive_button)

        main_layout.addLayout(input_layout)

        # Apply the stylesheet to the messages container widget
        self.messages_widget.setStyleSheet("""
            #messageListWidget {
                 background-color: lightblue; /* A light background for the chat area */
            }

            /* Style for sent message bubbles */
            QWidget#sent QTextBrowser {
                background-color: #DCF8C6; /* A light green for sent messages */
                border-radius: 10px;
                padding: 8px;
                 margin: 2px 0px; /* Vertical margin between bubbles */
                max-width: 75%;
                 /* Ensure the background is painted */
                border: 1px solid #FFFFFF; /* Small border can sometimes help rendering */
                
            }

            /* Style for received message bubbles */
            QWidget#received QTextBrowser {
                background-color: #FFFFFF; /* White for received messages */
                border-radius: 10px;
                padding: 8px;
                 margin: 2px 0px; /* Vertical margin between bubbles */
                max-width: 75%;
                 /* Ensure the background is painted */
                border: 1px solid #FFFFFF; /* Small border can sometimes help rendering */
                
                
            }

        """)

        # Connect signals to slots
        self.send_button.clicked.connect(self.send_message)
        self.receive_button.clicked.connect(self.receive_message)
        self.message_input.returnPressed.connect(self.send_message)


    def add_message(self, text, message_type):
        if not text:
            return

        message_bubble = MessageBubble(text, message_type)
        self.messages_layout.addWidget(message_bubble)

        # Use QTimer.singleShot to ensure scrolling happens after the layout is updated
        QTimer.singleShot(10, self.scroll_to_bottom)

    def scroll_to_bottom(self):
         self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())


    def send_message(self):
        message_text = self.message_input.text()
        self.add_message(message_text, "sent")
        self.message_input.clear()

    def receive_message(self):
        message_text = self.message_input.text()
        self.add_message(message_text, "received")
        self.message_input.clear()

# --- Application Entry Point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())