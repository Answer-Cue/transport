import requests
import os
from tqdm import tqdm


def download_file(
    url: str,
    save_path: str,
    show_progress: bool = True,
    resume: bool = True,
    use_tor: bool = False,
    tor_host: str = "127.0.0.1",
    tor_port: int = 9150,
    chunk_size: int = 8192,
):
    """
    url           : ダウンロード元URL
    save_path     : 保存ファイルパス
    show_progress : 進捗・残り時間表示
    resume        : 途中中断を再開するか
    use_tor       : Tor経由にするか
    """

    headers = {}
    downloaded_size = 0

    # Tor プロキシ設定
    proxies = None
    if use_tor:
        proxies = {
            "http": f"socks5h://{tor_host}:{tor_port}",
            "https": f"socks5h://{tor_host}:{tor_port}",
        }

    # 再開処理
    if resume and os.path.exists(save_path):
        downloaded_size = os.path.getsize(save_path)
        headers["Range"] = f"bytes={downloaded_size}-"

    response = requests.get(
        url,
        headers=headers,
        proxies=proxies,
        stream=True,
        timeout=60,
    )
    response.raise_for_status()

    # 全体サイズ
    total_size = response.headers.get("Content-Length")
    if total_size is not None:
        total_size = int(total_size) + downloaded_size

    mode = "ab" if resume and downloaded_size > 0 else "wb"

    progress_bar = None
    if show_progress:
        progress_bar = tqdm(
            total=total_size,
            initial=downloaded_size,
            unit="B",
            unit_scale=True,
            desc=os.path.basename(save_path),
        )

    with open(save_path, mode) as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                if progress_bar:
                    progress_bar.update(len(chunk))

    if progress_bar:
        progress_bar.close()

    print("ダウンロード完了:", save_path)
