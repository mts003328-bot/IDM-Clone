from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from core.download_worker import DownloadWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python IDM Clone")
        self.resize(800, 500)
        self.workers = {} # Keep track of active workers so they don't get garbage collected
        
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

        top_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste download URL here...")
        self.add_btn = QPushButton("Add Download")
        self.add_btn.clicked.connect(self.handle_add_url)
        
        top_layout.addWidget(self.url_input)
        top_layout.addWidget(self.add_btn)
        main_layout.addLayout(top_layout)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["File Name", "Size", "Progress", "Speed"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        main_layout.addWidget(self.table)

    def handle_add_url(self):
        url = self.url_input.text().strip()
        if not url:
            return
            
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem("Connecting..."))
        self.table.setItem(row, 1, QTableWidgetItem("--"))
        self.table.setItem(row, 2, QTableWidgetItem("0%"))
        self.table.setItem(row, 3, QTableWidgetItem("0 KB/s"))
        
        self.url_input.clear()
        
        # Create and start the background thread
        worker = DownloadWorker(url)
        
        # Connect signals to GUI updates
        worker.progress_signal.connect(lambda d, t: self.update_progress(row, d, t))
        worker.finished_signal.connect(lambda fn: self.download_finished(row, fn))
        worker.error_signal.connect(lambda err: self.download_error(row, err))
        
        # Store worker in dictionary so it isn't deleted by Python's garbage collector
        self.workers[row] = worker 
        worker.start()

    def update_progress(self, row, downloaded, total):
        if total > 0:
            percent = int((downloaded / total) * 100)
            self.table.setItem(row, 2, QTableWidgetItem(f"{percent}%"))
            
            # Basic speed calculation placeholder
            self.table.setItem(row, 3, QTableWidgetItem(f"{downloaded // 1024} KB total"))

    def download_finished(self, row, filename):
        self.table.setItem(row, 0, QTableWidgetItem(filename))
        self.table.setItem(row, 2, QTableWidgetItem("100%"))
        self.table.setItem(row, 3, QTableWidgetItem("Complete"))
        
        # Clean up worker
        if row in self.workers:
            self.workers[row].wait()
            del self.workers[row]

    def download_error(self, row, error_message):
        self.table.setItem(row, 0, QTableWidgetItem(f"Error: {error_message}"))
        self.table.setItem(row, 2, QTableWidgetItem("Failed"))
        
        if row in self.workers:
            self.workers[row].wait()
            del self.workers[row]