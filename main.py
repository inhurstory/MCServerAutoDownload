import os
import json
import shutil
import sys
import argparse
from api_tools.modrinthAPI import download_modrinth_plugin
from api_tools.spigotAPI import download_spigot_plugin_by_id
from api_tools.githubAPI import download_latest_github_release

# 修正 Windows 主控台下 print 特殊字元 (如 ®) 產生的 UnicodeEncodeError
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Keep the target explicit and overridable.  The old hard-coded value (21.1.2)
# made an otherwise current download look incompatible with the server.
MINECRAFT_VERSION = os.getenv("MINECRAFT_VERSION", "26.2")

parser = argparse.ArgumentParser(description="Download configured Minecraft plugins into staging.")
parser.add_argument("--source", choices=("all", "modrinth", "spigot", "github"), default="all")
parser.add_argument("--start", type=int, default=0, help="zero-based entry offset for a resumable batch")
parser.add_argument("--limit", type=int, default=None, help="maximum entries to process in this batch")
args = parser.parse_args()

if args.start < 0 or args.limit is not None and args.limit < 1:
    parser.error("--start must be >= 0 and --limit must be >= 1")


with open("plugins.json", encoding="utf-8") as f:
    cfg = json.load(f)

def selected_entries(source):
    entries = cfg[source]
    return entries[args.start:] if args.limit is None else entries[args.start:args.start + args.limit]

def distribute(filepath, servers):
    filename = os.path.basename(filepath)
    for server in servers:
        server_dir = os.path.join(DOWNLOAD_DIR, server)
        os.makedirs(server_dir, exist_ok=True)
        shutil.copy2(filepath, os.path.join(server_dir, filename))

# 處理 Modrinth 插件下載
if args.source in ("all", "modrinth"):
 print("\n===  下載 Modrinth 插件 ===")
for entry in selected_entries("modrinth") if args.source in ("all", "modrinth") else ():
    success, msg, filepath = download_modrinth_plugin(
        entry["id"], mc_version=MINECRAFT_VERSION, save_dir=DOWNLOAD_DIR
    )
    print(msg)
    if success and filepath:
        distribute(filepath, entry["servers"])

# 處理 Spigot 插件下載
if args.source in ("all", "spigot"):
 print("\n===  下載 Spigot 插件 ===")
for entry in selected_entries("spigot") if args.source in ("all", "spigot") else ():
    try:
        parts = entry["id"].rsplit(".", 1)
        if len(parts) != 2 or not parts[1].isdigit():
            print(f"【！】略過（非 slug.id 格式）：{entry['id']}")
            continue
        slug, resource_id = parts
        print(f"→ 正在下載 Spigot 插件：{slug} (ID: {resource_id})")
        filepath = download_spigot_plugin_by_id(resource_id, save_dir=DOWNLOAD_DIR)
        if filepath:
            distribute(filepath, entry["servers"])
    except Exception as e:
        print(f"【！】下載失敗（{entry['id']}）：{e}")

# 處理 GitHub 插件下載
if args.source in ("all", "github"):
 print("\n===  下載 GitHub 插件 ===")
for entry in selected_entries("github") if args.source in ("all", "github") else ():
    success, msg, filepath = download_latest_github_release(entry["repo"], save_dir=DOWNLOAD_DIR)
    print(msg)
    if success and filepath:
        distribute(filepath, entry["servers"])
