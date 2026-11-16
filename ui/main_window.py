import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QProgressBar, QLabel
)
from PySide6.QtCore import Qt
from core.downloader import Downloader
from core.download_worker import DownloadWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python IDM Clone")
        self.resize(650, 250)

        # State
        self.downloader = None
        self.worker = None

        # UI Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)

        # URL Row
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter download URL here (e.g., http://localhost:8765/dummy.dat)")
        self.start_btn = QPushButton("Start Download")
        self.start_btn.clicked.connect(self.start_download)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.start_btn)
        layout.addLayout(url_layout)

        # Status Label
        self.status_label = QLabel("Status: Idle")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.status_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

        # Control Buttons
        btn_layout = QHBoxLayout()
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.cancel_btn = QPushButton("Cancel")
        
        self.pause_btn.clicked.connect(self.pause_download)
        self.resume_btn.clicked.connect(self.resume_download)
        self.cancel_btn.clicked.connect(self.cancel_download)

        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.resume_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # Initialize button states
        self.set_idle_buttons()

    # --------------------------------------------------------- UI Helpers
    def set_idle_buttons(self):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

    def set_active_buttons(self):
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

    def set_paused_buttons(self):
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.resume_btn.setEnabled(True)

    # --------------------------------------------------------- Actions
    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.status_label.setText("Status: Error - Please enter a URL")
            return

        self.status_label.setText("Status: Starting...")
        self.progress_bar.setValue(0)
        self.set_active_buttons()

        self.downloader = Downloader(url)
        self._spawn_worker()

    def pause_download(self):
        if self.downloader:
            self.downloader.pause()
            self.status_label.setText("Status: Pausing...")

    def resume_download(self):
        if self.downloader:
            self.status_label.setText("Status: Resuming...")
            self.set_active_buttons()
            self._spawn_worker()

    def cancel_download(self):
        if self.downloader:
            self.downloader.cancel()
            self.status_label.setText("Status: Cancelling...")

    # --------------------------------------------------------- Worker Bridge
    def _spawn_worker(self):
        # Create a new worker thread. (QThread automatically bridges to the GUI thread).
        self.worker = DownloadWorker(self.downloader)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.start()

    # --------------------------------------------------------- Signals
    def update_progress(self, downloaded, total):
        if total > 0:
            percent = int((downloaded / total) * 100)
            self.progress_bar.setValue(percent)
            
            # Format bytes to MB
            mb_done = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_label.setText(f"Status: Downloading... ({mb_done:.1f} MB / {mb_total:.1f} MB)")

    def on_download_finished(self, status):
        if status == "completed":
            self.status_label.setText("Status: Download Complete! ✅")
            self.progress_bar.setValue(100)
            self.set_idle_buttons()
            
        elif status == "paused":
            self.status_label.setText("Status: Paused ⏸")
            self.set_paused_buttons()
            
        elif status == "cancelled":
            self.status_label.setText("Status: Cancelled ❌")
            self.progress_bar.setValue(0)
            self.set_idle_buttons()
            
        elif status == "failed":
            self.status_label.setText("Status: Failed (Check connection or URL) ⚠")
            self.set_idle_buttons()