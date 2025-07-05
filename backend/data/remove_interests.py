import json
from pathlib import Path

USERS_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/users.json"

def remove_interests_from_users():
    try:
        with open(Path(USERS_PATH), "r", encoding="utf-8") as f:
            users = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл {USERS_PATH} не найден")
        return
    except json.JSONDecodeError:
        print(f"Ошибка: Файл {USERS_PATH} содержит некорректный JSON")
        return

    updated_users = [{"id": user["id"]} for user in users]

    try:
        with open(Path(USERS_PATH), "w", encoding="utf-8") as f:
            json.dump(updated_users, f, ensure_ascii=False, indent=2)
        print(f"Поле interests успешно удалено из {USERS_PATH}")
        print(f"Обновлено пользователей: {len(updated_users)}")
    except Exception as e:
        print(f"Ошибка при сохранении {USERS_PATH}: {str(e)}")

if __name__ == "__main__":
    remove_interests_from_users()