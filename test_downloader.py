import os
import threading
import time
import http.server
import socketserver
from functools import partial
from core.downloader import Downloader

PORT = 8765
TEST_DIR = "test_server_files"
TEST_FILE = "dummy.dat"
DOWNLOAD_NAME = "downloaded_test.dat"

def start_local_server():
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=TEST_DIR)
    httpd = socketserver.TCPServer(("", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

def cleanup():
    for p in [DOWNLOAD_NAME, f"{DOWNLOAD_NAME}.state"]:
        try:
            os.remove(p)
        except OSError:
            pass

def test_full_download(url, expected_size):
    print("\n=== TEST 1: Full download ===")
    cleanup()
    d = Downloader(url)
    result = d.start_download(num_threads=4)
    assert result == "completed", f"expected completed, got {result}"
    assert os.path.getsize(DOWNLOAD_NAME) == expected_size
    assert not os.path.exists(f"{DOWNLOAD_NAME}.state")
    print("PASS")

def test_pause_then_resume(url, expected_size):
    print("\n=== TEST 2: Pause then resume ===")
    cleanup()
    d = Downloader(url)

    def pauser():
        time.sleep(0.05)
        d.pause()

    t = threading.Thread(target=pauser)
    t.start()
    result1 = d.start_download(num_threads=4)
    t.join()

    assert result1 == "paused", f"expected paused, got {result1}"
    assert os.path.exists(f"{DOWNLOAD_NAME}.state"), "state file should exist"

    result2 = d.resume(num_threads=4)
    assert result2 == "completed", f"expected completed on resume, got {result2}"
    print("PASS")

def test_cancel(url):
    print("\n=== TEST 3: Cancel ===")
    cleanup()
    d = Downloader(url)

    def canceller():
        time.sleep(0.05)
        d.cancel()

    t = threading.Thread(target=canceller)
    t.start()
    result = d.start_download(num_threads=4)
    t.join()

    assert result == "cancelled", f"expected cancelled, got {result}"
    print("PASS")

def test_bad_url():
    print("\n=== TEST 4: Bad URL ===")
    d = Downloader("http://127.0.0.1:1/does-not-exist")
    result = d.start_download()
    assert result == "failed", f"expected failed, got {result}"
    print("PASS")

if __name__ == "__main__":
    # 1. Ensure the server folder and dummy file exist
    os.makedirs(TEST_DIR, exist_ok=True)
    test_file_path = os.path.join(TEST_DIR, TEST_FILE)
    if not os.path.exists(test_file_path):
        print(f"Creating dummy file at {test_file_path}...")
        with open(test_file_path, "wb") as f:
            f.write(b'0' * 10_000_000)

    expected = os.path.getsize(test_file_path)
    url = f"http://localhost:{PORT}/{TEST_FILE}"

    # 2. Start server
    server = start_local_server()
    print(f"Local server running at: {url}")
    
    # 3. Patch probe to save as DOWNLOAD_NAME so we don't lock the server file
    import core.downloader
    original_probe = core.downloader.Downloader.probe
    def patched_probe(self):
        success = original_probe(self)
        if success:
            self.filename = DOWNLOAD_NAME
        return success
    core.downloader.Downloader.probe = patched_probe

    try:
        test_full_download(url, expected)
        test_pause_then_resume(url, expected)
        test_cancel(url)
        test_bad_url()
        print("\n🎉 ALL TESTS PASSED! The core engine is solid.")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("Check the [DEBUG] lines above to see why probe() failed.")
    finally:
        server.shutdown()