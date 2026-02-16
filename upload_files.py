"""
Загрузчик файлов в GitHub через API.
Все HTTP-запросы имеют timeout=10 (правила memory.md).
"""
import requests
import base64
import os
import sys
import time

TIMEOUT = 10
TOKEN = os.environ.get("GITHUB_TOKEN")
OWNER = "estruve"
REPO = "yasno-site"
BRANCH = "main"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCLUDE = {'deploy_github.py', 'upload_files.py', 'prompts.md', 'llms.txt', 'CNAME', 'robots.txt', 'sitemap.xml'}


def get_files():
    """Собираем файлы для загрузки (кроме уже загруженных)"""
    files = []
    for root, dirs, fnames in os.walk(SITE_DIR):
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__'}]
        for f in fnames:
            if f in EXCLUDE or f.startswith('.'):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, SITE_DIR).replace("\\", "/")
            files.append((rel, full))
    return files


def upload_one(rel_path, full_path):
    """Загружаем один файл"""
    try:
        with open(full_path, "rb") as f:
            raw = f.read()
        content_b64 = base64.b64encode(raw).decode("ascii")

        # Проверяем, существует ли файл
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{rel_path}"
        r = requests.get(url, headers=HEADERS, params={"ref": BRANCH}, timeout=TIMEOUT)

        payload = {"message": f"Add {rel_path}", "content": content_b64, "branch": BRANCH}

        if r.status_code == 200:
            # Файл существует — обновляем
            payload["sha"] = r.json()["sha"]
            payload["message"] = f"Update {rel_path}"

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
    print("  Загрузка файлов в estruve/yasno-site")
    print("=" * 50)

    files = get_files()
    print(f"Найдено {len(files)} файлов для загрузки\n")

    ok = 0
    fail = 0
    for i, (rel, full) in enumerate(files, 1):
        size_kb = os.path.getsize(full) / 1024
        sys.stdout.write(f"[{i}/{len(files)}] {rel} ({size_kb:.0f} KB) ... ")
        sys.stdout.flush()

        success, err = upload_one(rel, full)
        if success:
            print("OK")
            ok += 1
        else:
            print(f"FAIL ({err})")
            fail += 1

        time.sleep(0.5)

    print(f"\nИтого: {ok} загружено, {fail} ошибок")
    print(f"Репозиторий: https://github.com/{OWNER}/{REPO}")


if __name__ == "__main__":
    main()
