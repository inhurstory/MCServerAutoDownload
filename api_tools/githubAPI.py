import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
_raw = os.getenv("GITHUB_TOKEN", "")
_GITHUB_TOKEN = _raw if _raw.isascii() and _raw.strip() else None
if not _GITHUB_TOKEN:
    print("⚠️  未設定有效的 GITHUB_TOKEN")

def _get(url, **kwargs):
    headers = kwargs.pop("headers", {})
    if _GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {_GITHUB_TOKEN}"
    for _ in range(3):
        res = requests.get(url, headers=headers, **kwargs)
        if res.status_code != 429:
            return res
        wait = int(res.headers.get("Retry-After", 60))
        print(f"⏳ Rate limit，等待 {wait} 秒後重試...")
        time.sleep(wait)
    return res

def download_latest_github_release(repo, save_dir="downloads"):
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"

    try:
        response = _get(api_url)
        response.raise_for_status()
        data = response.json()

        tag_name = data.get("tag_name", "latest")
        assets = data.get("assets", [])
        if not assets:
            return False, f"❌ [{repo}] 無 assets 可供下載", None

        asset = assets[0]
        download_url = asset["browser_download_url"]
        filename = asset["name"]
        filepath = os.path.join(save_dir, filename)

        with _get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return True, f"✅ 已下載 [{repo}] 最新版 {tag_name} → {filename}", filepath

    except Exception as e:
        return False, f"❌ [{repo}] 錯誤：{str(e)}", None
