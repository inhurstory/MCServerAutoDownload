import requests
import os
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

def search_modrinth_project_id(slug):
    res = _get("https://api.modrinth.com/v2/search", params={"query": slug, "limit": 1})
    res.raise_for_status()
    hits = res.json()["hits"]
    if not hits:
        return None
    return hits[0]["project_id"]

def fetch_modrinth_versions(project_id):
    res = _get(f"https://api.modrinth.com/v2/project/{project_id}/version")
    res.raise_for_status()
    return res.json()

LOADER_PRIORITY = ["paper", "spigot", "bukkit"]

def find_version_for_mc(versions, mc_version):
    """回傳 (version, warn)；依 paper > spigot > bukkit 優先，僅接受這三種 loader"""
    valid = [v for v in versions if any(l in v["loaders"] for l in LOADER_PRIORITY)]
    if not valid:
        return None, False

    def sort_key(v):
        loader_rank = min(
            (LOADER_PRIORITY.index(l) for l in v["loaders"] if l in LOADER_PRIORITY),
            default=99
        )
        mc_match = 0 if mc_version in v["game_versions"] else 1
        return (mc_match, loader_rank)

    valid.sort(key=sort_key)
    best = valid[0]
    warn = mc_version not in best["game_versions"]
    return best, warn

def download_file(url, filepath):
    res = _get(url, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(res.content)

def download_modrinth_plugin(slug, mc_version, save_dir):
    try:
        project_id = search_modrinth_project_id(slug)
        if not project_id:
            return False, f"找不到插件：{slug}", None
        versions = fetch_modrinth_versions(project_id)
        if not versions:
            return False, f"找不到 {slug} 的任何版本", None

        version, warn = find_version_for_mc(versions, mc_version)
        if not version:
            return False, f"找不到 {slug} 的任何可下載版本", None

        file_info = version["files"][0]
        filename = file_info["filename"]
        filepath = os.path.join(save_dir, filename)

        download_file(file_info["url"], filepath)

        if warn:
            return True, f"⚠️ {slug} 沒有支援 MC {mc_version}，已下載較舊版本 {version['version_number']} - {filename}", filepath
        else:
            return True, f"✅ 已下載 {slug} - {filename}", filepath
    except Exception as e:
        return False, f"❌ 下載失敗（{slug}）：{e}", None
