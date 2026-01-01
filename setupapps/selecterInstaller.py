import os
import subprocess
import requests
import zipfile
import sys
import time

# --- 実行ファイルのあるディレクトリ ---
if getattr(sys, 'frozen', False):
    maindir = os.path.dirname(sys.executable)
    is_exe = True
else:
    maindir = os.path.dirname(os.path.abspath(__file__))
    is_exe = False

os.makedirs(maindir, exist_ok=True)
print("作業ディレクトリ:", maindir)

# --- ダウンロード関数（自作進捗表示） ---
def download_file(url, save_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total = int(response.headers.get('content-length', 0))
    downloaded = 0
    chunk_size = 1024

    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                # 進捗表示
                if total > 0:
                    percent = downloaded / total * 100
                    bar_length = 30
                    filled_length = int(bar_length * downloaded // total)
                    bar = '#' * filled_length + '-' * (bar_length - filled_length)
                    print(f'\r[{bar}] {percent:.1f}%', end='', flush=True)
    print()  # 改行

# --- ZIP ダウンロード＆展開 ---
zip_url = "https://raw.githubusercontent.com/Answer-Cue/transport/main/setupapps/selecter/_internal.zip"
zip_path = os.path.join(maindir, "selecter_internal.zip")
download_file(zip_url, zip_path)

with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall(maindir)
print("ZIP 展開完了")
os.remove(zip_path)
print("ZIP を削除しました")

# --- EXE ダウンロード ---
exe_url = "https://github.com/Answer-Cue/transport/raw/main/setupapps/selecter/selecter.exe"
exe_path = os.path.join(maindir, "selecter.exe")
download_file(exe_url, exe_path)
print("EXE ダウンロード完了")

# --- EXE 実行 ---
subprocess.Popen([exe_path])

# --- 自分自身を削除（exe の場合のみ） ---
if is_exe:
    self_path = sys.executable
    bat_path = os.path.join(maindir, "delete_self.bat")
    with open(bat_path, "w") as f:
        f.write(f"""@echo off
ping 127.0.0.1 -n 2 > nul
del "{self_path}"
del "%~f0"
""")
    subprocess.Popen([bat_path], shell=True)
