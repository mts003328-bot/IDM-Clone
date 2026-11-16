from PySide6.QtCore import QThread, Signal

class DownloadWorker(QThread):
    progress = Signal(int, int)
    finished = Signal(str)

    def __init__(self, downloader, num_threads=4):
        super().__init__()
        self.downloader = downloader
        self.num_threads = num_threads

    def run(self):
        result = self.downloader.start_download(
            num_threads=self.num_threads,
            progress_callback=self._on_progress,
        )
        self.finished.emit(result)

    def _on_progress(self, downloaded, total):
        self.progress.emit(downloaded, total)