import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QTableWidget, QAbstractItemView
)
from PySide6.QtCore import Qt
from core.download_worker import DownloadWorker
from ui.styles import DARK_STYLE # Import our new style

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python IDM Clone")
        self.resize(900, 500) # Made slightly wider for the new column
        self.workers = {} 
        self.row_data = {} # Keep track of last time and bytes for speed calc
        
        # Apply the imported style
        self.setStyleSheet(DARK_STYLE)

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

        # Table setup - NOW 5 COLUMNS
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["File Name", "Size", "Progress", "Speed", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False) # Hide row numbers
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Make table read-only
        main_layout.addWidget(self.table)

    def format_bytes(self, size):
        """Converts bytes to KB, MB, GB for display"""
        if size == 0: return "0 B"
        power = 1024
        n = 0
        dict_suffix = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
        while size >= power and n < 4:
            size /= power
            n += 1
        return f"{size:.2f} {dict_suffix[n]}"

    def handle_add_url(self):
        url = self.url_input.text().strip()
        if not url:
            return
            
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 40) # Make rows slightly taller for buttons
        
        self.table.setItem(row, 0, QTableWidgetItem("Connecting..."))
        self.table.setItem(row, 1, QTableWidgetItem("--"))
        self.table.setItem(row, 2, QTableWidgetItem("0%"))
        self.table.setItem(row, 3, QTableWidgetItem("0 KB/s"))
        
        # Add the action buttons
        self.table.setCellWidget(row, 4, self.create_action_buttons(row))
        
        self.url_input.clear()
        
        # Setup tracking for speed
        self.row_data[row] = {"last_bytes": 0, "last_time": time.time()}
        
        worker = DownloadWorker(url)
        worker.progress_signal.connect(lambda d, t: self.update_progress(row, d, t))
        worker.finished_signal.connect(lambda fn: self.download_finished(row, fn))
        worker.error_signal.connect(lambda err: self.download_error(row, err))
        
        self.workers[row] = worker 
        worker.start()

    def create_action_buttons(self, row):
        """Creates the Pause and Cancel buttons for a specific row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        pause_btn = QPushButton("Pause")
        pause_btn.setObjectName("pauseBtn")
        pause_btn.clicked.connect(lambda: self.handle_pause(row))
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(lambda: self.handle_cancel(row))
        
        layout.addWidget(pause_btn)
        layout.addWidget(cancel_btn)
        layout.addStretch()
        return widget

    def update_progress(self, row, downloaded, total):
        if total > 0:
            # 1. Update Progress %
            percent = int((downloaded / total) * 100)
            self.table.setItem(row, 2, QTableWidgetItem(f"{percent}%"))
            
            # 2. Update Size (we only need to set this once, but setting it continuously is fine)
            self.table.setItem(row, 1, QTableWidgetItem(self.format_bytes(total)))
            
            # 3. Calculate Speed
            current_time = time.time()
            time_diff = current_time - self.row_data[row]["last_time"]
            
            if time_diff >= 1.0: # Update speed every 1 second to avoid flickering
                bytes_diff = downloaded - self.row_data[row]["last_bytes"]
                speed = bytes_diff / time_diff
                self.table.setItem(row, 3, QTableWidgetItem(f"{self.format_bytes(speed)}/s"))
                
                # Reset trackers for the next second
                self.row_data[row]["last_time"] = current_time
                self.row_data[row]["last_bytes"] = downloaded

    def handle_pause(self, row):
        # We will connect this to the engine later
        print(f"TODO: Pause download at row {row}")

    def handle_cancel(self, row):
        # We will connect this to the engine later
        print(f"TODO: Cancel download at row {row}")

    def download_finished(self, row, filename):
        self.table.setItem(row, 0, QTableWidgetItem(filename))
        self.table.setItem(row, 2, QTableWidgetItem("100%"))
        self.table.setItem(row, 3, QTableWidgetItem("Complete"))
        
        # Remove the action buttons when finished
        self.table.removeCellWidget(row, 4)
        
        if row in self.workers:
            self.workers[row].wait()
            del self.workers[row]

    def download_error(self, row, error_message):
        self.table.setItem(row, 0, QTableWidgetItem(f"Error: {error_message}"))
        self.table.setItem(row, 2, QTableWidgetItem("Failed"))
        self.table.removeCellWidget(row, 4)
        
        if row in self.workers:
            self.workers[row].wait()
            del self.workers[row]