import requests
import os
import time
import hashlib

def _get(url, **kwargs):
    for _ in range(3):
        res = requests.get(url, **kwargs)
        if res.status_code != 429:
            return res
        wait = int(res.headers.get("Retry-After", 60))
        print(f"Rate limit，等待 {wait} 秒後重試...")
        time.sleep(wait)
    return res

def search_modrinth_project_id(slug):
    # A search result is only a best-effort text match and can silently point
    # at a different project.  Modrinth accepts a project slug directly.
    res = _get(f"https://api.modrinth.com/v2/project/{slug}")
    res.raise_for_status()
    project = res.json()
    # Some Paper-compatible projects are categorised as a mod by Modrinth.
    # The exact slug is the identity check; loader filtering happens later.
    normalise = lambda value: "".join(ch for ch in value.lower() if ch.isalnum())
    if normalise(project.get("slug", "")) != normalise(slug):
        return None
    return project["id"]

def fetch_modrinth_versions(project_id):
    res = _get(f"https://api.modrinth.com/v2/project/{project_id}/version")
    res.raise_for_status()
    return res.json()

LOADER_PRIORITY = ["paper", "spigot", "bukkit"]

def find_version_for_mc(versions, mc_version):
    # 回傳 (version, warn)；僅接受 Paper/Spigot/Bukkit 可用版本。
    valid = [v for v in versions if any(l in v["loaders"] for l in LOADER_PRIORITY)]
    if not valid:
        return None, False

    def sort_key(v):
        loader_rank = min(
            (LOADER_PRIORITY.index(l) for l in v["loaders"] if l in LOADER_PRIORITY),
            default=99
        )
        mc_match = 0 if mc_version in v["game_versions"] else 1
        
        # 提取 date_published 的數字作為發布順序依據 (時間戳記負數，越新則值越小排越前)
        date_str = v.get("date_published", "")
        digits = "".join(c for c in date_str if c.isdigit())
        date_rank = -int(digits) if digits else 0
        
        return (mc_match, loader_rank, date_rank)

    matching = [v for v in valid if mc_version in v["game_versions"]]
    if matching:
        # For an exact target match, prefer the native Paper artifact.
        matching.sort(key=sort_key)
        best = matching[0]
        warn = False
    else:
        # Do not mistake an older Paper build for "latest" merely because its
        # loader has a higher priority.  With no target match, publication date
        # is the best available version signal.
        valid.sort(key=lambda v: (sort_key(v)[2], sort_key(v)[1]))
        best = valid[0]
        warn = True
    return best, warn

def download_file(url, filepath):
    res = _get(url, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(res.content)

def _select_primary_jar(files):
    jars = [item for item in files if item.get("filename", "").lower().endswith(".jar")]
    if not jars:
        return None
    # Modrinth marks the intended runtime artifact as primary.  This avoids
    # selecting an API, sources, or auxiliary artifact merely because it is
    # first in the response.
    primary = [item for item in jars if item.get("primary")]
    return (primary or jars)[0]

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

        file_info = _select_primary_jar(version["files"])
        if not file_info:
            return False, f"{slug} 的選定版本沒有可安裝的 JAR", None
        filename = file_info["filename"]
        filepath = os.path.join(save_dir, filename)

        download_file(file_info["url"], filepath)
        expected_hash = file_info.get("hashes", {}).get("sha512")
        if expected_hash:
            with open(filepath, "rb") as downloaded:
                actual_hash = hashlib.sha512(downloaded.read()).hexdigest()
            if actual_hash.lower() != expected_hash.lower():
                os.remove(filepath)
                return False, f"【！】{slug} 下載雜湊不符，已拒絕檔案", None

        if warn:
            return True, f"【！】{slug} 尚未宣告支援 MC {mc_version}；已下載最新可用發行版 {version['version_number']} - {filename}", filepath
        else:
            return True, f"已下載 {slug} - {filename}", filepath
    except Exception as e:
        return False, f"【！】下載失敗（{slug}）：{e}", None
