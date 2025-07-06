import random
import pandas as pd
import json
from pathlib import Path

COURSES_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/courses.json"
USERS_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/users.json"
USER_COURSES_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/user_courses.json"

tag_categories = {
    "programming": ["python", "C#", "C++", "GoLang", "async programming"],
    "web-development": ["frontend", "backend", "html", "css", "javascript", "web-development"],
    "databases": ["databases", "sql", "postgreSQL"],
    "data-science": ["data-science", "machine-learning", "NLP", "computer vision"],
    "devops": ["devops", "cloud-computing", "CI/CD", "Docker"],
    "cybersecurity": ["backend", "mobile-development", "anti-cheats", "software architecture"],
    "software architecture": ["OOP", "functional programming", "procedural programming"],
    "testing": ["auto-tests", "manual testing", "integration tests", "load test"],
}

difficulties = ["beginner", "intermediate", "advanced"]

def get_logical_tags(category, num_tags):
    primary_tags = tag_categories[category]
    tags = random.sample(primary_tags, min(len(primary_tags), num_tags))
    if category == "databases" and "sql" not in tags:
        tags.append("sql")
    if category == "web-development" and "html" not in tags and random.random() < 0.5:
        tags.append("html")
    return tags

def generate_course_name(category, difficulty):
    category_name = category.replace("-", " ").title()
    difficulty_name = difficulty.title()
    return f"{category_name} for {difficulty_name}"

def generate_courses(num_courses):
    courses = []
    seen_combinations = set()

    for i in range(1, num_courses + 1):
        attempts = 0
        max_attempts = 100
        while attempts < max_attempts:
            category = random.choice(list(tag_categories.keys()))
            num_tags = random.randint(1, 3)
            tags = get_logical_tags(category, num_tags)
            difficulty = random.choice(difficulties)
            tags_tuple = tuple(sorted(tags))
            combination = (tags_tuple, difficulty)

            if combination not in seen_combinations:
                seen_combinations.add(combination)
                course_name = generate_course_name(category, difficulty)
                courses.append({
                    "id": i,
                    "name": course_name,
                    "difficulty": difficulty,
                    "tags": tags
                })
                break
            attempts += 1
        if attempts == max_attempts:
            print(f"Предупреждение: не удалось создать уникальный курс для id {i}")

    return courses


# Генерация курсов
num_courses = 150
courses = generate_courses(num_courses)

# Список всех возможных тегов
possible_tags = [tag for tags in tag_categories.values() for tag in tags]

# Генерация пользователей
num_users = 200
users = []
for user_id in range(1, num_users + 1):
    num_interests = random.randint(2, 4)  # Увеличено число интересов
    interests = random.sample(possible_tags, num_interests)
    users.append({"id": f"user{user_id}", "interests": interests})

# Генерация взаимодействий с учетом зависимостей сложности
user_courses = []
for user in users:
    user_id = user["id"]
    interests = set(user["interests"])
    num_interactions = random.randint(8, 20)  # Увеличено число взаимодействий

    # Группируем курсы по категориям для проверки зависимостей сложности
    courses_by_category = {}
    for category in tag_categories:
        courses_by_category[category] = [
            course for course in courses
            if any(tag in tag_categories[category] for tag in course["tags"])
        ]

    selected_courses = []
    for _ in range(num_interactions):
        # Выбираем категорию, связанную с интересами пользователя
        relevant_categories = [
            cat for cat in tag_categories
            if any(tag in interests for tag in tag_categories[cat])
        ]
        if not relevant_categories:
            relevant_categories = list(tag_categories.keys())
        category = random.choice(relevant_categories)

        # Проверяем, какие курсы пользователь может пройти в этой категории
        available_courses = []
        beginner_courses = [
            c for c in courses_by_category[category] if c["difficulty"] == "beginner"
        ]
        intermediate_courses = [
            c for c in courses_by_category[category] if c["difficulty"] == "intermediate"
        ]
        advanced_courses = [
            c for c in courses_by_category[category] if c["difficulty"] == "advanced"
        ]

        # Проверяем завершенные курсы и их успеваемость
        user_completed_courses = [
            uc for uc in user_courses
            if uc["user_id"] == user_id and uc["completed"]
        ]
        completed_beginner = any(
            uc["course_id"] in [c["id"] for c in beginner_courses]
            and uc["performance"] >= 60
            for uc in user_completed_courses
        )
        completed_intermediate = any(
            uc["course_id"] in [c["id"] for c in intermediate_courses]
            and uc["performance"] >= 60
            for uc in user_completed_courses
        )

        # Логика доступности курсов
        if beginner_courses:
            available_courses.extend(beginner_courses)
        if completed_beginner or random.random() < 0.8:  # 80% шанс для intermediate
            available_courses.extend(intermediate_courses)
        if completed_beginner and completed_intermediate:
            available_courses.extend(advanced_courses)

        if not available_courses:
            available_courses = beginner_courses

        # Выбираем курс из доступных, исключая уже выбранные
        available_courses = [c for c in available_courses if c["id"] not in [sc["id"] for sc in selected_courses]]
        if not available_courses:
            continue
        course = random.choice(available_courses)
        selected_courses.append(course)

        course_tags = set(course["tags"])
        common_tags = course_tags.intersection(interests)
        completion_prob = 0.95 if common_tags else 0.7  # Увеличена вероятность завершения
        completed = random.random() < completion_prob

        # Генерация успеваемости и оценки
        if completed:
            if common_tags:
                performance = random.randint(80, 100)  # Высокая успеваемость
                score = random.choices([4, 5], weights=[0.2, 0.8])[0]  # 80% шанс на score=5
            else:
                performance = random.randint(60, 90)
                score = random.choices([3, 4, 5], weights=[0.1, 0.4, 0.5])[0]  # 50% шанс на score=4, 40% на score=5
        else:
            performance = 0
            score = 0

        user_courses.append({
            "user_id": user_id,
            "course_id": course["id"],
            "completed": completed,
            "score": 5,
            "performance": performance
        })

# Сохранение данных
with open(Path(COURSES_PATH), "w", encoding="utf-8") as f:
    json.dump(courses, f, ensure_ascii=False, indent=2)

with open(Path(USERS_PATH), "w", encoding="utf-8") as f:
    json.dump(users, f, ensure_ascii=False, indent=2)

with open(Path(USER_COURSES_PATH), "w", encoding="utf-8") as f:
    json.dump(user_courses, f, ensure_ascii=False, indent=2)

# Проверка результатов
df_courses = pd.DataFrame(courses)
df_users = pd.DataFrame(users)
df_user_courses = pd.DataFrame(user_courses)

# Статистика по данным
print(f"Количество курсов: {len(df_courses)}")
print(f"Количество пользователей: {len(df_users)}")
print(f"Количество взаимодействий: {len(df_user_courses)}")
print(f"Количество завершенных курсов: {len(df_user_courses[df_user_courses['completed']])}")
print(
    f"Количество курсов с score >= 4: {len(df_user_courses[(df_user_courses['completed']) & (df_user_courses['score'] >= 4)])}")
print(
    f"Количество курсов с performance >= 60: {len(df_user_courses[(df_user_courses['completed']) & (df_user_courses['performance'] >= 60)])}")
print(f"Распределение score:\n{df_user_courses[df_user_courses['completed']]['score'].value_counts().to_dict()}")
print(
    f"Распределение performance (для завершенных):\n{df_user_courses[df_user_courses['completed']]['performance'].describe().to_dict()}")
print(
    f"Распределение курсов по категориям:\n{df_courses['name'].apply(lambda x: x.split(' for ')[0]).value_counts().to_dict()}")