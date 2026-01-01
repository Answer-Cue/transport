from pathlib import Path
import requests
import time
import sys


class GitTextSource:
    def __init__(self, url: str, timeout: int = 15):
        self.url = url
        self.timeout = timeout

    def load_downloads(self):
        r = requests.get(self.url, timeout=self.timeout)
        r.raise_for_status()

        scope = {}
        exec(r.text, scope)

        downloads = scope.get("downloads")
        if not downloads:
            raise RuntimeError("downloads が定義されていません")

        return downloads


class DownloadTask:
    def __init__(self, url: str, filename: str, base_dir: Path):
        self.url = url
        self.filename = filename
        self.save_path = base_dir / "downloads" / filename
        self.save_path.parent.mkdir(parents=True, exist_ok=True)

    def download(self):
        downloaded = self.save_path.stat().st_size if self.save_path.exists() else 0
        headers = {"Range": f"bytes={downloaded}-"} if downloaded > 0 else {}

        with requests.get(self.url, stream=True, headers=headers, timeout=30) as r:
            r.raise_for_status()

            total_size = int(r.headers.get("Content-Length", 0))
            if "Content-Range" in r.headers:
                total_size += downloaded

            if total_size > 0 and downloaded >= total_size:
                print(f"{self.filename}: 既にダウンロード済み")
                return

            start_time = time.time()
            mode = "ab" if downloaded > 0 else "wb"

            with open(self.save_path, mode) as f:
                for chunk in r.iter_content(8192):
                    if not chunk:
                        continue

                    f.write(chunk)
                    downloaded += len(chunk)

                    self._print_progress(downloaded, total_size, start_time)

        print(f"\r{self.filename}: 100.00% | ダウンロード完了")

    def _print_progress(self, downloaded, total_size, start_time):
        elapsed = time.time() - start_time
        if elapsed <= 0 or total_size <= 0:
            return

        speed = downloaded / elapsed
        remaining = (total_size - downloaded) / speed if speed > 0 else 0
        percent = downloaded * 100 / total_size

        print(
            f"\r{self.filename}: "
            f"{percent:6.2f}% | "
            f"{speed/1024/1024:5.2f} MB/s | "
            f"残り {remaining:5.1f} 秒",
            end=""
        )


class DownloadManager:
    def __init__(self, source: GitTextSource, base_dir: Path):
        self.source = source
        self.base_dir = base_dir

    def run(self):
        downloads = self.source.load_downloads()
        for url, name in downloads:
            task = DownloadTask(url, name, self.base_dir)
            task.download()


# --------------------
# エントリーポイント
# --------------------
if __name__ == "__main__":


    if getattr(sys, "frozen", False):
        BASE_DIR = Path(sys.executable).resolve().parent
    else:
        BASE_DIR = Path(__file__).resolve().parent


    source = GitTextSource(
        "https://raw.githubusercontent.com/Answer-Cue/transport/main/downloadcontents.txt"
    )

    manager = DownloadManager(source, BASE_DIR)
    manager.run()
