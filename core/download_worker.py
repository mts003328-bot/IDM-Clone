from PySide6.QtCore import QThread, Signal
from core.downloader import Downloader

class DownloadWorker(QThread):
    # Define signals to communicate with the GUI
    progress_signal = Signal(int, int) # (downloaded_bytes, total_bytes)
    finished_signal = Signal(str)      # (filename)
    error_signal = Signal(str)         # (error_message)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.downloader = Downloader(url)

    def run(self):
        """This runs in the background thread."""
        try:
            # We pass a function that emits our signal
            success = self.downloader.start_download(
                num_threads=4, 
                progress_callback=lambda downloaded, total: self.progress_signal.emit(downloaded, total)
            )
            
            if success:
                self.finished_signal.emit(self.downloader.filename)
            else:
                self.error_signal.emit("Download failed or server doesn't support ranges.")
                
        except Exception as e:
            self.error_signal.emit(str(e))