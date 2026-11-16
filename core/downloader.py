import requests
import concurrent.futures
import os

class Downloader:
    def __init__(self, url):
        self.url = url
        self.file_size = 0
        self.supports_ranges = False
        self.filename = "downloaded_file"
        
        # Setup a session to reuse connections (faster)
        self.session = requests.Session()

    def probe(self):
        print(f"Probing URL: {self.url}")
        try:
            response = self.session.head(self.url, allow_redirects=True, timeout=10)
            
            if response.status_code == 405 or 'Content-Length' not in response.headers:
                response = self.session.get(self.url, headers={'Range': 'bytes=0-0'}, stream=True, timeout=10)

            content_length = response.headers.get('Content-Length')
            if content_length:
                self.file_size = int(content_length)
                print(f"✅ File Size: {self.file_size} bytes")

            accept_ranges = response.headers.get('Accept-Ranges')
            if accept_ranges == 'bytes' or 'Content-Range' in response.headers:
                self.supports_ranges = True
                print("✅ Server SUPPORTS multi-threaded downloads.")
            
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition and 'filename=' in content_disposition:
                self.filename = content_disposition.split('filename=')[1].strip('"\'')
            else:
                self.filename = self.url.split('/')[-1].split('?')[0] or "downloaded_file"
                
            print(f"📁 Output Filename: {self.filename}")
            return True
        except Exception as e:
            print(f"❌ Error probing URL: {e}")
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

    def _download_chunk(self, start_byte, end_byte, filename):
        """Downloads a specific byte range and writes it to the file at the correct offset."""
        headers = {'Range': f'bytes={start_byte}-{end_byte}'}
        try:
            response = self.session.get(self.url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            
            # Open file in 'r+b' (read/write binary) and seek to the correct start position
            with open(filename, 'r+b') as f:
                f.seek(start_byte)
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"Error downloading chunk {start_byte}-{end_byte}: {e}")
            return False

    def start_download(self, num_threads=4):
        """Orchestrates the multi-threaded download."""
        if not self.probe():
            return False
            
        chunks = self.calculate_chunks(num_threads)
        if not chunks:
            print("⚠️ Cannot multi-thread. Falling back to single-thread (Not implemented yet).")
            return False

        print(f"🚀 Starting download with {num_threads} threads...")

        # 1. Pre-allocate the file with the exact file size so threads can write to specific offsets
        with open(self.filename, 'wb') as f:
            f.seek(self.file_size - 1)
            f.write(b'\0')

        # 2. Start the threads using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for start, end in chunks:
                futures.append(executor.submit(self._download_chunk, start, end, self.filename))
            
            # Wait for all threads to finish
            for future in concurrent.futures.as_completed(futures):
                if not future.result():
                    print("❌ A chunk failed to download.")
                    return False

        print("🎉 Download complete!")
        return True


# --- Test Block (Runs only if you execute this file directly) ---
if __name__ == "__main__":
    test_url = "https://proof.ovh.net/files/10Mb.dat" # Let's test with a 10MB file
    d = Downloader(test_url)
    d.start_download(num_threads=4)