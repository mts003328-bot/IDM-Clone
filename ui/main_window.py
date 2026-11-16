from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python IDM Clone")
        self.resize(800, 500)
        
        # Apply a basic dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; color: white; }
            QLineEdit { padding: 8px; background-color: #3c3f41; color: white; border: 1px solid #555; }
            QPushButton { padding: 8px 15px; background-color: #4caf50; color: white; border: none; border-radius: 3px; }
            QPushButton:hover { background-color: #45a049; }
            QTableWidget { background-color: #3c3f41; color: white; gridline-color: #555; }
            QHeaderView::section { background-color: #2b2b2b; color: white; padding: 4px; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top bar: URL input and Add button
        top_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste download URL here...")
        self.add_btn = QPushButton("Add Download")
        self.add_btn.clicked.connect(self.handle_add_url)
        
        top_layout.addWidget(self.url_input)
        top_layout.addWidget(self.add_btn)
        main_layout.addLayout(top_layout)

        # Download list (Table)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["File Name", "Size", "Progress", "Speed"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        main_layout.addWidget(self.table)

    def handle_add_url(self):
        url = self.url_input.text()
        if not url:
            return
            
        # Add a row to the table just to see it working
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem("Fetching data..."))
        self.table.setItem(row_position, 1, QTableWidgetItem("--"))
        self.table.setItem(row_position, 2, QTableWidgetItem("0%"))
        self.table.setItem(row_position, 3, QTableWidgetItem("0 KB/s"))
        
        self.url_input.clear()