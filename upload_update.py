"""
Загрузка обновлённых файлов (Punycode fix + Mobile menu + FOUC fix).
"""
import requests
import base64
import os
import sys
import time

TIMEOUT = 30  # Увеличен для index.html (~76KB)
TOKEN = os.environ.get("GITHUB_TOKEN")
OWNER = "estruve"
REPO = "yasno-site"
BRANCH = "main"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

SITE_DIR = os.path.dirname(os.path.abspath(__file__))

# Только изменённые файлы
CHANGED_FILES = [
    "robots.txt",
    "sitemap.xml",
    "icicle.html",
    "neon.html",
    "belt-light.html",
    "string-light.html",
    "index.html",
]


def upload_one(rel_path, full_path):
    try:
        with open(full_path, "rb") as f:
            raw = f.read()
        content_b64 = base64.b64encode(raw).decode("ascii")

        url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{rel_path}"
        r = requests.get(url, headers=HEADERS, params={"ref": BRANCH}, timeout=TIMEOUT)

        payload = {"message": f"Update {rel_path} — fix Punycode + mobile menu", "content": content_b64, "branch": BRANCH}

        if r.status_code == 200:
            payload["sha"] = r.json()["sha"]

        r2 = requests.put(url, json=payload, headers=HEADERS, timeout=TIMEOUT)

        if r2.status_code in [200, 201]:
            return True, ""
        else:
            return False, f"{r2.status_code}: {r2.json().get('message', '')}"
    except requests.exceptions.Timeout:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 50)
    print("  Загрузка обновлений в estruve/yasno-site")
    print("=" * 50)

    ok = 0
    fail = 0
    for i, fname in enumerate(CHANGED_FILES, 1):
        full = os.path.join(SITE_DIR, fname)
        size_kb = os.path.getsize(full) / 1024
        sys.stdout.write(f"[{i}/{len(CHANGED_FILES)}] {fname} ({size_kb:.0f} KB) ... ")
        sys.stdout.flush()

        success, err = upload_one(fname, full)
        if success:
            print("OK")
            ok += 1
        else:
            print(f"FAIL ({err})")
            fail += 1

        time.sleep(0.5)

    print(f"\nИтого: {ok} загружено, {fail} ошибок")
    print(f"Сайт: https://github.com/{OWNER}/{REPO}")


if __name__ == "__main__":
    main()
