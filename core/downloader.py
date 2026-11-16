import requests
from concurrent.futures import ThreadPoolExecutor
import threading

class Downloader:
    def __init__(self, url):
        self.url = url
        self.file_size = 0
        self.supports_ranges = False
        self.filename = "downloaded_file"
        self.session = requests.Session()
        
        # Thread safety
        self.downloaded_bytes = 0
        self._lock = threading.Lock()

    def probe(self):
        try:
            response = self.session.head(self.url, allow_redirects=True, timeout=10)
            if response.status_code == 405 or 'Content-Length' not in response.headers:
                response = self.session.get(self.url, headers={'Range': 'bytes=0-0'}, stream=True, timeout=10)

            content_length = response.headers.get('Content-Length')
            if content_length:
                self.file_size = int(content_length)

            accept_ranges = response.headers.get('Accept-Ranges')
            if accept_ranges == 'bytes' or 'Content-Range' in response.headers:
                self.supports_ranges = True
            
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition and 'filename=' in content_disposition:
                self.filename = content_disposition.split('filename=')[1].strip('"\'')
            else:
                self.filename = self.url.split('/')[-1].split('?')[0] or "downloaded_file"
            return True
        except Exception as e:
            print(f"Error probing URL: {e}")
            return False

    def calculate_chunks(self, num_threads=4):
        if not self.supports_ranges or self.file_size == 0:
            return []
        chunk_size = self.file_size // num_threads
        chunks = []
        for i in range(num_threads):
            start = i * chunk_size
            end = self.file_size - 1 if i == num_threads - 1 else start + chunk_size - 1
            chunks.append((start, end))
        return chunks

    def _download_chunk(self, start_byte, end_byte, filename, progress_callback):
        headers = {'Range': f'bytes={start_byte}-{end_byte}'}
        try:
            response = self.session.get(self.url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(filename, 'r+b') as f:
                f.seek(start_byte)
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    # Safely update the shared byte counter
                    with self._lock:
                        self.downloaded_bytes += len(chunk)
                        if progress_callback:
                            # Send current downloaded bytes and total size
                            progress_callback(self.downloaded_bytes, self.file_size)
            return True
        except Exception as e:
            print(f"Error chunk: {e}")
            return False

    def start_download(self, num_threads=4, progress_callback=None):
        if not self.probe():
            return False
            
        chunks = self.calculate_chunks(num_threads)
        if not chunks:
            return False

        # Pre-allocate file
        with open(self.filename, 'wb') as f:
            f.seek(self.file_size - 1)
            f.write(b'\0')

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for start, end in chunks:
                futures.append(executor.submit(self._download_chunk, start, end, self.filename, progress_callback))
            
            for future in concurrent.futures.as_completed(futures):
                if not future.result():
                    return False

        return True