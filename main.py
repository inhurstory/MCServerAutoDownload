import os
import json
import shutil
from api_tools.modrinthAPI import download_modrinth_plugin
from api_tools.spigotAPI import download_spigot_plugin_by_id
from api_tools.githubAPI import download_latest_github_release

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

with open("plugins.json", encoding="utf-8") as f:
    cfg = json.load(f)

def distribute(filepath, servers):
    filename = os.path.basename(filepath)
    for server in servers:
        server_dir = os.path.join(DOWNLOAD_DIR, server)
        os.makedirs(server_dir, exist_ok=True)
        shutil.copy2(filepath, os.path.join(server_dir, filename))

# 處理 Modrinth 插件下載
print("\n=== 🔽 下載 Modrinth 插件 ===")
for entry in cfg["modrinth"]:
    success, msg, filepath = download_modrinth_plugin(entry["id"], mc_version="1.21.5", save_dir=DOWNLOAD_DIR)
    print(msg)
    if success and filepath:
        distribute(filepath, entry["servers"])

# 處理 Spigot 插件下載
print("\n=== 🔽 下載 Spigot 插件 ===")
for entry in cfg["spigot"]:
    try:
        parts = entry["id"].rsplit(".", 1)
        if len(parts) != 2 or not parts[1].isdigit():
            print(f"⚠️  略過（非 slug.id 格式）：{entry['id']}")
            continue
        slug, resource_id = parts
        print(f"→ 正在下載 Spigot 插件：{slug} (ID: {resource_id})")
        filepath = download_spigot_plugin_by_id(resource_id, save_dir=DOWNLOAD_DIR)
        if filepath:
            distribute(filepath, entry["servers"])
    except Exception as e:
        print(f"❌ 下載失敗（{entry['id']}）：{e}")

# 處理 GitHub 插件下載
print("\n=== 🔽 下載 GitHub 插件 ===")
for entry in cfg["github"]:
    success, msg, filepath = download_latest_github_release(entry["repo"], save_dir=DOWNLOAD_DIR)
    print(msg)
    if success and filepath:
        distribute(filepath, entry["servers"])
