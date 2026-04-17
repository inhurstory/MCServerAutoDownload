import requests
import os
import re
import time

def _get(url, **kwargs):
    for _ in range(3):
        res = requests.get(url, **kwargs)
        if res.status_code != 429:
            return res
        wait = int(res.headers.get("Retry-After", 60))
        print(f"⏳ Rate limit，等待 {wait} 秒後重試...")
        time.sleep(wait)
    return res

def download_spigot_plugin_by_id(resource_id, save_dir="."):
    headers = {"User-Agent": "Mozilla/5.0"}

    # 1. 直接用 resource ID 取得插件資訊（不靠名稱搜尋）
    res = _get(f"https://api.spiget.org/v2/resources/{resource_id}", headers=headers)
    if res.status_code != 200:
        print(f"❌ 找不到插件 ID：{resource_id}（HTTP {res.status_code}）")
        return False
    plugin_title = res.json()["name"]

    # 2. 撈取版本資訊
    res = _get(f"https://api.spiget.org/v2/resources/{resource_id}/versions", headers=headers)
    if res.status_code != 200 or not res.json():
        print(f"❌ 無法取得 {plugin_title} 的版本資訊")
        return False
    version_name = res.json()[0]["name"]

    # 3. 下載
    res = _get(f"https://api.spiget.org/v2/resources/{resource_id}/download", headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://www.spigotmc.org/resources/{resource_id}/"
    }, allow_redirects=True)
    if res.status_code != 200:
        print(f"❌ 下載失敗：HTTP {res.status_code}")
        return False

    # 4. 儲存（移除 Windows 非法字元）
    safe_title = re.sub(r'[\\/:*?"<>|\[\]]', '_', plugin_title)
    filename = f"{safe_title}-{version_name}.jar"
    save_path = os.path.join(save_dir, filename)
    with open(save_path, "wb") as f:
        f.write(res.content)

    print(f"✅ 已下載最新版本：{plugin_title} v{version_name}")
    print(f"📦 檔案儲存於：{save_path}")
    return save_path
