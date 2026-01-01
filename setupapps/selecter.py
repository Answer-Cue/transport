import pygame
import requests
import sys
import os
import time
import ast
import re
import threading
import tkinter as tk
from tkinter import messagebox

# --- tkinter を非表示で初期化 ---
root = tk.Tk()
root.withdraw()

pygame.init()

# --------------------
# exe化対応と保存先
# --------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DL_DIR = os.path.join(BASE_DIR, "dlfiles")
os.makedirs(DL_DIR, exist_ok=True)

# --------------------
# アイコン設定
# --------------------
icon_path = os.path.join(BASE_DIR, "icon.png")
if os.path.exists(icon_path):
    icon_img = pygame.image.load(icon_path)
else:
    icon_img = None

# --------------------
# 画面設定
# --------------------
W, H = 800, 450
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("ビルド選択")
if icon_img:
    pygame.display.set_icon(icon_img)
clock = pygame.time.Clock()
font = pygame.font.SysFont("meiryo", 36)
small_font = pygame.font.SysFont("meiryo", 24)

# --------------------
# メニュー設定
# --------------------
MAIN_MENU = ["パッケージビルド", "任意ビルド"]
items = MAIN_MENU.copy()
menu_state = "MAIN"
index = 0

BASE_X = W // 2
spacing = 420
offset = 0.0
velocity = 0.0

PACKAGE_URL = "https://raw.githubusercontent.com/Answer-Cue/transport/main/packageFol/"

# --------------------
# 任意ビルド入力欄
# --------------------
input_boxes = ["", ""]
active_box = 0
message = ""

# --------------------
# パッケージビルド用
# --------------------
package_items = []
package_content = []

# --------------------
# フルダウンロード用管理
# --------------------
full_dl_package_list = []  # フルDL対象パッケージ名リスト
full_dl_current_index = 0  # 現在処理中のパッケージ

# --------------------
# パッケージデータ読み込み
# --------------------
def load_package_menu():
    url = PACKAGE_URL + "selectobjects.txt?t=" + str(int(time.time()))
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    return [line.strip() for line in r.text.splitlines() if line.strip()]

def load_package_file(name):
    url = PACKAGE_URL + f"{name}.txt?t={int(time.time())}"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    text = r.text
    m = re.search(r"downloads\s*=\s*(\[.*\])", text, re.DOTALL)
    if not m:
        raise ValueError("downloads リストが見つかりません")
    list_text = m.group(1)
    downloads = ast.literal_eval(list_text)
    return downloads

# --------------------
# ダウンロード管理クラス
# --------------------
class DownloadTask:
    def __init__(self, url, save_path):
        self.url = url
        self.save_path = save_path
        self.file_name = os.path.basename(save_path)
        self.progress = 0.0
        self.done = False
        self.success = False
        self.thread = threading.Thread(target=self.download)
        self.thread.start()

    def download(self):
        try:
            downloaded_size = 0
            if os.path.exists(self.save_path):
                downloaded_size = os.path.getsize(self.save_path)

            headers = {}
            if downloaded_size > 0:
                headers['Range'] = f'bytes={downloaded_size}-'

            with requests.get(self.url, stream=True, headers=headers, timeout=10) as r:
                if r.status_code in [200, 206]:
                    total_length = r.headers.get('content-length')
                    if total_length is None:
                        with open(self.save_path, "ab") as f:
                            f.write(r.content)
                        self.progress = 1
                    else:
                        total_length = int(total_length) + downloaded_size
                        downloaded = downloaded_size
                        chunk_size = 8192
                        with open(self.save_path, "ab") as f:
                            for chunk in r.iter_content(chunk_size=chunk_size):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    self.progress = downloaded / total_length
                    self.success = True
                else:
                    print(f"[失敗] {self.file_name}: サーバーがRangeに対応していません")
                    self.success = False
        except Exception as e:
            print(f"[失敗] {self.file_name}: {e}")
            self.success = False
        finally:
            self.done = True

# --------------------
# グローバル変数
# --------------------
download_tasks = []
download_in_progress = False

# --------------------
# クリップボードボタン
# --------------------
button_w, button_h = 40, 30
button_color = (100, 100, 200)
button_hover = (150, 150, 250)

def draw_clip_button(x, y):
    mouse_pos = pygame.mouse.get_pos()
    rect = pygame.Rect(x, y, button_w, button_h)
    color = button_hover if rect.collidepoint(mouse_pos) else button_color
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, (255,255,255), rect, 2)
    surf = small_font.render("C", True, (255,255,255))
    screen.blit(surf, (x + 12, y + 2))
    return rect

# --------------------
# メインループ
# --------------------
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # --- キー入力 ---
        if not download_in_progress:
            if e.type == pygame.KEYDOWN:
                if menu_state in ["MAIN", "PACKAGE"]:
                    if e.key == pygame.K_RIGHT:
                        index = (index + 1) % len(items)
                    if e.key == pygame.K_LEFT:
                        index = (index - 1) % len(items)
                    if e.key == pygame.K_RETURN:
                        selected = items[index]
                        if menu_state == "MAIN":
                            if selected == "パッケージビルド":
                                try:
                                    package_items = load_package_menu()
                                    items = package_items.copy() + ["フルダウンロード", "戻る"]
                                except:
                                    items = ["読み込み失敗", "戻る"]
                                menu_state = "PACKAGE"
                                index = 0
                                offset = 0
                                velocity = 0
                                package_content = []
                            elif selected == "任意ビルド":
                                menu_state = "ANY_BUILD_INPUT"
                                input_boxes = ["", ""]
                                active_box = 0
                                message = ""
                        elif menu_state == "PACKAGE":
                            if selected == "戻る":
                                items = MAIN_MENU.copy()
                                menu_state = "MAIN"
                                index = 0
                                offset = 0
                                velocity = 0
                                package_content = []
                            elif selected == "フルダウンロード":
                                full_dl_package_list = package_items.copy()
                                full_dl_current_index = 0
                                # 最初のパッケージ開始
                                if full_dl_package_list:
                                    pkg_name = full_dl_package_list[full_dl_current_index]
                                    try:
                                        contents = load_package_file(pkg_name)
                                        package_dir = os.path.join(DL_DIR, pkg_name)
                                        os.makedirs(package_dir, exist_ok=True)
                                        download_tasks = [DownloadTask(url, os.path.join(package_dir, save_name)) for url, save_name in contents]
                                        download_in_progress = True
                                    except Exception as ex:
                                        print(f"[失敗] {pkg_name}: {ex}")
                            else:
                                try:
                                    package_content = load_package_file(selected)
                                    package_dir = os.path.join(DL_DIR, selected)
                                    os.makedirs(package_dir, exist_ok=True)
                                    download_tasks = [DownloadTask(url, os.path.join(package_dir, save_name)) for url, save_name in package_content]
                                    download_in_progress = True
                                except Exception as ex:
                                    print(f"[失敗] {ex}")
                                    package_content = []

                    if e.key == pygame.K_ESCAPE:
                        items = MAIN_MENU.copy()
                        menu_state = "MAIN"
                        index = 0
                        offset = 0
                        velocity = 0
                        package_content = []

                elif menu_state == "ANY_BUILD_INPUT":
                    if e.key == pygame.K_TAB:
                        active_box = (active_box + 1) % 2
                    elif e.key == pygame.K_ESCAPE:
                        menu_state = "MAIN"
                        index = 0
                        offset = 0
                        velocity = 0
                    elif e.key == pygame.K_RETURN:
                        url = input_boxes[0].strip()
                        save_name = input_boxes[1].strip()
                        if url and save_name:
                            save_path = os.path.join(DL_DIR, save_name)
                            download_tasks = [DownloadTask(url, save_path)]
                            download_in_progress = True
                    elif e.key == pygame.K_BACKSPACE:
                        input_boxes[active_box] = input_boxes[active_box][:-1]
                    else:
                        if len(e.unicode) == 1:
                            input_boxes[active_box] += e.unicode

        # --- マウスクリックでクリップボードボタン ---
        if e.type == pygame.MOUSEBUTTONDOWN and menu_state == "ANY_BUILD_INPUT":
            for i in range(2):
                rect = pygame.Rect(100, 100 + i*60, 600, 40)
                btn_rect = pygame.Rect(rect.right + 10, rect.y + 5, button_w, button_h)
                if btn_rect.collidepoint(e.pos):
                    try:
                        input_boxes[i] = root.clipboard_get()
                    except:
                        pass

    # --- バネ移動 ---
    if not download_in_progress and menu_state in ["MAIN", "PACKAGE"]:
        target = -index * spacing
        velocity += (target - offset) * 0.12
        velocity *= 0.7
        offset += velocity

    # --- 描画 ---
    screen.fill((20, 20, 30))

    if not download_in_progress:
        if menu_state in ["MAIN", "PACKAGE"]:
            for i, text in enumerate(items):
                cx = BASE_X + i * spacing + offset
                cy = H // 2
                dist = abs(cx - BASE_X)
                scale = max(0.7, 1 - dist / 600)
                color = (255,230,180) if i == index else (180,180,180)
                surf = font.render(text, True, color)
                w,h = surf.get_size()
                surf = pygame.transform.smoothscale(surf,(int(w*scale),int(h*scale)))
                rect = surf.get_rect(center=(cx, cy))
                screen.blit(surf, rect)

        elif menu_state == "ANY_BUILD_INPUT":
            for i in range(2):
                rect = pygame.Rect(100, 100 + i*60, 600, 40)
                color = (255,255,255) if active_box==i else (180,180,180)
                pygame.draw.rect(screen, color, rect, 2)
                text_surf = small_font.render(input_boxes[i], True, (255,255,255))
                screen.blit(text_surf, (rect.x+5, rect.y+5))
                draw_clip_button(rect.right + 10, rect.y + 5)

            info_surf2 = small_font.render("上:URL  下:保存名  TAB切替 ENTER保存 ESC戻る", True, (200,200,200))
            screen.blit(info_surf2, (50, 30))

    # --- ダウンロード進捗 ---
    if download_in_progress and download_tasks:
        finished_tasks = sum(task.done for task in download_tasks)
        bar_width = 600
        bar_height = 20
        y_start = 150
        for i, task in enumerate(download_tasks):
            y = y_start + i*40
            pygame.draw.rect(screen, (100,100,100), (100, y, bar_width, bar_height))
            pygame.draw.rect(screen, (50,200,50), (100, y, int(bar_width*task.progress), bar_height))
            text = small_font.render(f"{task.file_name} {int(task.progress*100)}%", True, (255,255,255))
            screen.blit(text, (100, y - 25))

        if finished_tasks == len(download_tasks):
            # フルダウンロードなら次のパッケージへ
            if full_dl_package_list:
                full_dl_current_index += 1
                if full_dl_current_index < len(full_dl_package_list):
                    pkg_name = full_dl_package_list[full_dl_current_index]
                    try:
                        contents = load_package_file(pkg_name)
                        package_dir = os.path.join(DL_DIR, pkg_name)
                        os.makedirs(package_dir, exist_ok=True)
                        download_tasks = [DownloadTask(url, os.path.join(package_dir, save_name)) for url, save_name in contents]
                    except Exception as ex:
                        print(f"[失敗] {pkg_name}: {ex}")
                else:
                    # 全部終わり
                    download_in_progress = False
                    download_tasks = []
                    full_dl_package_list = []
                    message = "すべてのダウンロード完了"
                    try:
                        messagebox.showinfo("ダウンロード完了", message)
                    except:
                        pass
            else:
                download_in_progress = False
                download_tasks = []
                message = "ダウンロード完了"
                try:
                    messagebox.showinfo("ダウンロード完了", message)
                except:
                    pass

    pygame.display.flip()
    clock.tick(60)
