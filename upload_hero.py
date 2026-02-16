"""Загрузчик одного большого файла с увеличенным таймаутом"""
import requests
import base64
import os

TIMEOUT = 60  # 60 секунд для большого файла
TOKEN = os.environ.get("GITHUB_TOKEN")
OWNER = "eestruve"
REPO = "yasno-site"
BRANCH = "main"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

FILE_PATH = "assets/images/hero_winter_house.png"
FULL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), FILE_PATH.replace("/", os.sep))

print(f"Загружаю {FILE_PATH} ({os.path.getsize(FULL_PATH)/1024:.0f} KB)...")

with open(FULL_PATH, "rb") as f:
    content_b64 = base64.b64encode(f.read()).decode("ascii")

url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{FILE_PATH}"

# Проверяем существование
r = requests.get(url, headers=HEADERS, params={"ref": BRANCH}, timeout=TIMEOUT)
payload = {"message": f"Add {FILE_PATH}", "content": content_b64, "branch": BRANCH}
if r.status_code == 200:
    payload["sha"] = r.json()["sha"]

r2 = requests.put(url, json=payload, headers=HEADERS, timeout=TIMEOUT)
if r2.status_code in [200, 201]:
    print(f"✅ Загружено!")
else:
    print(f"❌ Ошибка: {r2.status_code} — {r2.json().get('message', '')}")
