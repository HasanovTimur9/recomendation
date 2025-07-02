from pathlib import Path
from typing import Any
import json

COURSES_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/courses.json"
USERS_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/users.json"
USER_COURSES_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/user_courses.json"


def load_json(path: str) -> Any:
    with open(Path(path), "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: Any, path: str) -> None:
    with open(Path(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_raw_data():
    courses = load_json(COURSES_PATH)
    users = load_json(USERS_PATH)
    user_courses = load_json(USER_COURSES_PATH)
    return courses, users, user_courses

def save_raw_data(courses: list, users: list, user_courses: list) -> None:
    save_json(courses, COURSES_PATH)
    save_json(users, USERS_PATH)
    save_json(user_courses, USER_COURSES_PATH)


