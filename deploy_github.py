"""
Скрипт для деплоя сайта Ясно на GitHub Pages.
Создаёт репозиторий и загружает все файлы через GitHub API.

ПРАВИЛА (из memory.md):
- Все сетевые запросы имеют timeout=10
- Циклы защищены от бесконечного выполнения
- Вывод прогресса для мониторинга
"""
import requests
import base64
import os
import sys
import time

# Таймаут для всех запросов (секунды)
TIMEOUT = 10

TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = "yasno-site"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

SITE_DIR = os.path.dirname(os.path.abspath(__file__))

# Файлы, которые НЕ нужно загружать
EXCLUDE_FILES = {'deploy_github.py', 'prompts.md', 'llms.txt'}
EXCLUDE_DIRS = {'.git', '__pycache__'}


def check_connection():
    """Фаза 1: Проверяем подключение к GitHub API"""
    print("[Тест 1/3] Проверяю подключение к GitHub API...")
    try:
        r = requests.get("https://api.github.com", timeout=TIMEOUT)
        print(f"   ✅ GitHub API доступен (статус: {r.status_code})")
        return True
    except requests.exceptions.Timeout:
        print("   ❌ Таймаут! GitHub API не отвечает за 10 секунд.")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False


def check_token():
    """Фаза 2: Проверяем валидность токена"""
    print("[Тест 2/3] Проверяю токен...")
    try:
        r = requests.get("https://api.github.com/user", headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            user = r.json()
            print(f"   ✅ Токен валиден! Аккаунт: {user['login']}")
            return user['login']
        else:
            print(f"   ❌ Токен невалиден! Статус: {r.status_code}")
            return None
    except requests.exceptions.Timeout:
        print("   ❌ Таймаут при проверке токена.")
        return None
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None


def check_files():
    """Фаза 3: Проверяем файлы для загрузки"""
    print("[Тест 3/3] Проверяю файлы для загрузки...")
    files = get_all_files()
    print(f"   ✅ Найдено {len(files)} файлов для загрузки")
    for rel_path, _ in files:
        print(f"      📄 {rel_path}")
    return files


def get_all_files():
    """Собирает все файлы для загрузки"""
    files = []
    for root, dirs, filenames in os.walk(SITE_DIR):
        # Исключаем ненужные директории
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        for f in filenames:
            if f in EXCLUDE_FILES or f.startswith('.'):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, SITE_DIR).replace("\\", "/")
            files.append((rel_path, full_path))
    return files


def create_repo(username):
    """Создаёт репозиторий на GitHub"""
    print("\n📦 Создаю репозиторий...")
    try:
        r = requests.post(
            "https://api.github.com/user/repos",
            json={
                "name": REPO_NAME,
                "description": "Ясно — Ландшафтное освещение в Москве",
                "public": True
            },
            headers=HEADERS,
            timeout=TIMEOUT
        )
        if r.status_code == 201:
            print(f"   ✅ Репозиторий создан: {r.json()['html_url']}")
            return f"{username}/{REPO_NAME}"
        elif r.status_code == 422:
            print(f"   ℹ️  Репозиторий уже существует: {username}/{REPO_NAME}")
            return f"{username}/{REPO_NAME}"
        else:
            print(f"   ❌ Ошибка: {r.status_code} — {r.json().get('message', '')}")
            return None
    except requests.exceptions.Timeout:
        print("   ❌ Таймаут при создании репозитория.")
        return None
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None


def upload_file(full_name, rel_path, full_path):
    """Загружает один файл в репозиторий"""
    try:
        with open(full_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        r = requests.put(
            f"https://api.github.com/repos/{full_name}/contents/{rel_path}",
            json={"message": f"Add {rel_path}", "content": content},
            headers=HEADERS,
            timeout=TIMEOUT
        )

        if r.status_code in [200, 201]:
            return "✅"
        elif r.status_code == 422:
            # Файл уже существует — обновляем
            get_r = requests.get(
                f"https://api.github.com/repos/{full_name}/contents/{rel_path}",
                headers=HEADERS,
                timeout=TIMEOUT
            )
            if get_r.status_code == 200:
                sha = get_r.json()['sha']
                r2 = requests.put(
                    f"https://api.github.com/repos/{full_name}/contents/{rel_path}",
                    json={"message": f"Update {rel_path}", "content": content, "sha": sha},
                    headers=HEADERS,
                    timeout=TIMEOUT
                )
                return "✅ (обновлён)" if r2.status_code in [200, 201] else f"❌ ({r2.status_code})"
            return f"❌ (не удалось получить SHA)"
        else:
            return f"❌ ({r.status_code})"
    except requests.exceptions.Timeout:
        return "❌ (таймаут)"
    except Exception as e:
        return f"❌ ({e})"


def upload_all_files(full_name, files):
    """Загружает все файлы с прогрессом"""
    print(f"\n📤 Загружаю {len(files)} файлов...")
    success = 0
    failed = 0
    max_files = len(files)  # Защита от бесконечного цикла

    for i, (rel_path, full_path) in enumerate(files[:max_files], 1):
        sys.stdout.write(f"   [{i}/{max_files}] {rel_path} ... ")
        sys.stdout.flush()
        result = upload_file(full_name, rel_path, full_path)
        print(result)

        if "✅" in result:
            success += 1
        else:
            failed += 1

        time.sleep(0.5)  # Пауза для API rate limit

    print(f"\n   Итого: ✅ {success} загружено, ❌ {failed} ошибок")
    return failed == 0


def enable_pages(full_name):
    """Включает GitHub Pages"""
    print("\n🌐 Включаю GitHub Pages...")
    try:
        r = requests.post(
            f"https://api.github.com/repos/{full_name}/pages",
            json={"source": {"branch": "main", "path": "/"}},
            headers={**HEADERS, "Accept": "application/vnd.github.switcheroo-preview+json"},
            timeout=TIMEOUT
        )
        if r.status_code in [201, 409]:
            print("   ✅ GitHub Pages включён!")
            return True
        else:
            print(f"   ⚠️  Не удалось включить автоматически ({r.status_code})")
            print("   → Включите вручную: Settings → Pages → Branch: main → Save")
            return False
    except requests.exceptions.Timeout:
        print("   ⚠️  Таймаут. Включите вручную: Settings → Pages → Branch: main → Save")
        return False


def main():
    print("=" * 55)
    print("   🚀 Деплой сайта Ясно на GitHub Pages")
    print("=" * 55)

    # Фаза 1-3: Проверки
    if not check_connection():
        print("\n⛔ Невозможно подключиться к GitHub. Проверьте интернет.")
        return

    username = check_token()
    if not username:
        print("\n⛔ Токен невалиден. Создайте новый на github.com/settings/tokens")
        return

    files = check_files()
    if not files:
        print("\n⛔ Нет файлов для загрузки.")
        return

    # Деплой
    full_name = create_repo(username)
    if not full_name:
        return

    if upload_all_files(full_name, files):
        enable_pages(full_name)

    # Итог
    print()
    print("=" * 55)
    print("   🎉 ГОТОВО!")
    print(f"   📁 Репозиторий: https://github.com/{full_name}")
    print(f"   🌐 Сайт: https://{username}.github.io/{REPO_NAME}/")
    print()
    print("   Для привязки домена ясно.москва:")
    print("   Settings → Pages → Custom domain → ясно.москва")
    print("=" * 55)


if __name__ == "__main__":
    main()
