本專案是給 Minecraft 服主用的，你是不是受夠了每次版本更新都要手動重新下載所有插件？
本專案提供一鍵下載 Spigot / Modrinth / GitHub 上插件的最新版本，並自動按伺服器分類分發。

A one-click tool for Minecraft server owners to automatically download the latest versions of plugins from Spigot, Modrinth, and GitHub — and distribute them to each server folder automatically.

---

## 設置 / Settings

參考範例填入
plugins.json
.env

---

# 執行 / Run

./run.sh        # Linux / macOS
run.bat         # Windows

---

## GitHub Token

GitHub API 限制為 60 次/小時（未認證）。填入 Token 後提升至 5000 次/小時。

GitHub's unauthenticated limit is 60 req/hour. With a token it raises to 5000 req/hour.

產生方式 / How to generate:
**GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**
不需要勾選任何 scope / No scopes required for public repos.

---

## 付費插件 / Premium Plugins

SpigotMC 付費資源無法自動下載（API 回傳 403）。請手動下載。

Premium SpigotMC resources cannot be downloaded automatically (API returns 403). Download them manually.
