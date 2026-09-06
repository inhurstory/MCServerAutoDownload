import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
_raw = os.getenv("GITHUB_TOKEN", "")
_GITHUB_TOKEN = _raw if _raw.isascii() and _raw.strip() else None
if not _GITHUB_TOKEN:
    print("【！】未設定有效的 GITHUB_TOKEN")

def _get(url, **kwargs):
    headers = kwargs.pop("headers", {})
    if _GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {_GITHUB_TOKEN}"
    for _ in range(3):
        res = requests.get(url, headers=headers, **kwargs)
        # An expired or revoked token must not block access to public releases.
        # Retry once without credentials; callers still get the normal HTTP
        # error if the repository itself is private or unavailable.
        if res.status_code == 401 and "Authorization" in headers:
            print("【！】GITHUB_TOKEN 無效，改用公開 GitHub API 重試")
            headers = {key: value for key, value in headers.items() if key.lower() != "authorization"}
            res = requests.get(url, headers=headers, **kwargs)
        if res.status_code != 429:
            return res
        wait = int(res.headers.get("Retry-After", 60))
        print(f"Rate limit，等待 {wait} 秒後重試...")
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
            return False, f"【！】[{repo}] 無 assets 可供下載", None

        # 優先過濾出執行用的主 Jar 檔 (排除開發包與其他伺服器平台如 velocity, bungee, fabric)
        jar_assets = [a for a in assets if a["name"].endswith(".jar")]
        if jar_assets:
            # 排除非 Bukkit/Paper 平台的關鍵字
            exclude_keywords = ["api", "sources", "javadoc", "dev", "lib", "velocity", "bungeecord", "bungee", "sponge", "fabric", "forge", "neoforge"]
            primary_jars = [a for a in jar_assets if not any(x in a["name"].lower() for x in exclude_keywords)]
            if primary_jars:
                # 若其中有明確包含 paper/spigot/bukkit 關鍵字，優先選擇
                preferred_jars = [a for a in primary_jars if any(x in a["name"].lower() for x in ["paper", "spigot", "bukkit"])]
                if preferred_jars:
                    asset = max(preferred_jars, key=lambda a: a.get("size", 0))
                else:
                    asset = max(primary_jars, key=lambda a: a.get("size", 0))
            else:
                asset = max(jar_assets, key=lambda a: a.get("size", 0))
        else:
            asset = assets[0]
        download_url = asset["browser_download_url"]
        filename = asset["name"]
        filepath = os.path.join(save_dir, filename)

        with _get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return True, f"已下載 [{repo}] 最新版 {tag_name} → {filename}", filepath

    except Exception as e:
        return False, f"【！】[{repo}] 錯誤：{str(e)}", None
