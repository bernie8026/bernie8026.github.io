"""
main.py
~~~~~~~~

這個腳本會抓取《崩壞 3rd》Fandom 更新日誌頁面，檢測最新版本號，並在有新版本時生成一篇 Markdown 攻略文章。文章會保存於 `posts/` 目錄，格式符合典型静態站組生器的前置資訊（front matter）。

工作流程：

1. 下載更新日誌頁面內容。
2. 找到第一個以 "Version" 開頭的連結（例如 "Version 8.5"），解析版本號。
3. 收集該版本號下的條目，直到遇到下一個版本標題。
4. 與本地 `data/last_version.txt` 進行比較，如果版本號不同，代表有新版本，則生成 Markdown 文件並更新 `last_version.txt`。

此腳本預期在 GitHub Actions 或其他定時任務中運行。
"""

import datetime
import os
import re
import sys
from typing import List, Tuple, Optional

import requests
from bs4 import BeautifulSoup


UPDATE_URL = "https://honkaiimpact3.fandom.com/wiki/Update_Log"
LAST_VERSION_FILE = os.path.join("data", "last_version.txt")
POSTS_DIR = "posts"


def fetch_latest_version_and_notes() -> Tuple[Optional[str], List[str]]:
    """抓取更新日誌頁面並返回最新的版本號及其更新項目列表。

    Returns:
        Tuple of (version, notes). version 為最新版本號（例如 '8.5'），notes 為每一條更新內容的文字列表。如果未找到版本號，返回 (None, [])。
    """
    try:
        response = requests.get(UPDATE_URL, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch update page: {e}", file=sys.stderr)
        return None, []

    soup = BeautifulSoup(response.text, "html.parser")

    # 找到第一個以 "Version" 開頭的鏈接
    version_link = soup.find("a", string=lambda s: s and s.startswith("Version"))
    if not version_link:
        return None, []

    # 提取版本號，例如 "Version 8.5" -> "8.5"
    match = re.search(r"Version\s*([\d.]+)", version_link.get_text())
    if not match:
        return None, []
    version = match.group(1).strip()

    # 收集該版本的更新條目：從版本連接的父元組開始運筆兄弟元組直到遇到下一個版本標題
    notes: List[str] = []
    for sibling in version_link.parent.next_siblings:
        # 當遇到下一個版本連接時停止
        if getattr(sibling, "name", None) == "a" and sibling.get_text().startswith("Version"):
            break
        # 獲取文字內容
        text = ''
        if hasattr(sibling, "get_text"):
            text = sibling.get_text().strip()
        else:
            # 處理 NavigableString
            text = str(sibling).strip()
        if text:
            # 部分內容可能包含多個項目，用換行符或 • 分割
            parts = [item.strip("\n\u2022 ") for item in re.split(r"[\n\u2022]+", text) if item.strip()]
            notes.extend(parts)
    return version, notes


def read_last_version() -> Optional[str]:
    """讀取 data/last_version.txt 內記錄的版本號。"""
    try:
        with open(LAST_VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def write_last_version(version: str) -> None:
    """寫入最新的版本號至 data/last_version.txt。"""
    os.makedirs(os.path.dirname(LAST_VERSION_FILE), exist_ok=True)
    with open(LAST_VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(version)


def create_post(version: str, notes: List[str]) -> str:
    """生成 Markdown 文章並返回其路徑。"""
    os.makedirs(POSTS_DIR, exist_ok=True)
    date_str = datetime.date.today().isoformat()
    # 生成檔名：例如 2025-10-30-v8-5.md
    safe_version = version.replace(".", "-")
    filename = f"{date_str}-v{safe_version}.md"
    path = os.path.join(POSTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"title: \"Honkai Impact Patch {version}\"\n")
        f.write(f"date: {date_str}\n")
        f.write("---\n\n")
        f.write(f"檢測到新版本 **{version}**，以下為更新摘要：\n\n")
        for note in notes:
            f.write(f"- {note}\n")
        f.write("\n更多資訊請參考官方更新日誌：\n")
        f.write(f"{UPDATE_URL}\n")
    return path


def main() -> None:
    version, notes = fetch_latest_version_and_notes()
    if version is None:
        print("未能取得版本號，結束腳本。")
        return
    last_version = read_last_version()
    if last_version == version:
        print(f"\u6c92有新版本，當前版本為 {version}。")
        return
    # 生成文章並更新版本號
    post_path = create_post(version, notes)
    write_last_version(version)
    print(f"\u5df2生成 {post_path}，並更新版本號為 {version}。")


if __name__ == "__main__":
    main()
