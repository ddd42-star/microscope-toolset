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
from PyQt5 import QtWidgets, QtCore, QtGui # QtGui is still needed for QPalette, but basic widgets are in QtWidgets

class MCPWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.resize(700, 250) # Increased height to better show chat area
        widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout() # Use QVBoxLayout for main vertical arrangement


        # --- Chat Area ---
        self.le = QtWidgets.QLineEdit()
        self.le.returnPressed.connect(self.append_text)

        self.tab = QtWidgets.QTextBrowser()
        self.tab.setAcceptRichText(True)
        self.tab.setOpenExternalLinks(True)

        self.clear_btn = QtWidgets.QPushButton('Clear')
        self.clear_btn.pressed.connect(self.clear_text)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tab, 0)
        vbox.addWidget(self.le, 1)

        # --- Options Bar ---
        option_layout = QtWidgets.QHBoxLayout() # QHBoxLayout for horizontal arrangement of options

        llm_language_label = QtWidgets.QLabel("LLM Language:") # Add labels for clarity
        self.llm_language = QtWidgets.QComboBox()
        llms_labels = ["gpt-4.1-mini", "gemini", "other"]
        self.llm_language.addItems(llms_labels)

        toolsets_label = QtWidgets.QLabel("Toolsets:") # Add labels for clarity
        self.toolsets = QtWidgets.QComboBox()
        tools_labels = ["microscope-toolset", "search publications", "LLM"]
        self.toolsets.addItems(tools_labels)

        option_layout.addWidget(llm_language_label)
        option_layout.addWidget(self.llm_language)
        option_layout.addWidget(toolsets_label)
        option_layout.addWidget(self.toolsets)
        option_layout.addWidget(self.clear_btn)
        option_layout.addStretch() # Add stretch to push widgets to the left

        # --- Arrange Layouts in Main Layout ---
        main_layout.addLayout(vbox)
        main_layout.addLayout(option_layout)    # Add options horizontal layout below

        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        self.setWindowTitle("MCP Window") # Set window title

    def append_text(self):
        text = self.le.text()
        self.tab.append(text)
        self.le.clear()

    def clear_text(self):
        self.tab.clear()

# if __name__ == '__main__':
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     main_window = MCPWindow()
#     main_window.show()
#     sys.exit(app.exec_())