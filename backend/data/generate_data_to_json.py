import random
import pandas as pd
import json
from pathlib import Path

COURSES_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/courses.json"
USERS_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/users.json"
USER_COURSES_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/user_courses.json"

possible_tags = [
    "python", "data-science", "machine-learning", "web-development", "databases",
    "cloud-computing", "devops", "cybersecurity", "frontend", "backend",
    "mobile-development", "game-development", "sql", "javascript", "html", "css"
]

tag_categories = {
    "programming": ["python", "javascript", "sql"],
    "web-development": ["frontend", "backend", "html", "css", "javascript", "web-development"],
    "databases": ["databases", "sql"],
    "data-science": ["data-science", "machine-learning", "python"],
    "devops": ["devops", "cloud-computing"],
    "other": ["cybersecurity", "mobile-development", "game-development"]
}

difficulties = ["beginner", "intermediate", "advanced"]


def get_logical_tags(category, num_tags):
    primary_tags = tag_categories[category]
    other_tags = [tag for tags in tag_categories.values() for tag in tags if tag not in primary_tags]
    tags = random.sample(primary_tags, min(len(primary_tags), num_tags))
    if len(tags) < num_tags:
        additional_tags = random.sample(other_tags, num_tags - len(tags))
        tags.extend(additional_tags)
    if category == "databases" and "sql" not in tags:
        tags.append("sql")
    if category == "web-development" and "html" not in tags and random.random() < 0.5:
        tags.append("html")
    return tags


def generate_course_name(primary_tag, difficulty):
    tag_name = primary_tag.replace("-", " ").title()
    difficulty_name = difficulty.title()
    return f"{tag_name} for {difficulty_name}"


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
                primary_tag = tag_categories[category][0]  # Первый тег из категории как основной
                course_name = generate_course_name(primary_tag, difficulty)
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


num_courses = 150
courses = generate_courses(num_courses)

num_users = 200
users = []
for user_id in range(1, num_users + 1):
    num_interests = random.randint(1, 3)
    interests = random.sample(possible_tags, num_interests)
    users.append({"id": f"user{user_id}", "interests": interests})

user_courses = []
for user in users:
    user_id = user["id"]
    interests = set(user["interests"])
    num_interactions = random.randint(5, 10)
    selected_courses = random.sample(courses, min(num_interactions, len(courses)))
    for course in selected_courses:
        course_tags = set(course["tags"])
        common_tags = course_tags.intersection(interests)
        completion_prob = 0.8 if common_tags else 0.3
        completed = random.random() < completion_prob
        score = random.randint(3, 5) if completed and common_tags else random.randint(1, 3) if completed else 0
        user_courses.append({
            "user_id": user_id,
            "course_id": course["id"],
            "completed": completed,
            "score": score
        })

with open(Path(COURSES_PATH), "w", encoding="utf-8") as f:
    json.dump(courses, f, ensure_ascii=False, indent=2)

with open(Path(USERS_PATH), "w", encoding="utf-8") as f:
    json.dump(users, f, ensure_ascii=False, indent=2)

with open(Path(USER_COURSES_PATH), "w", encoding="utf-8") as f:
    json.dump(user_courses, f, ensure_ascii=False, indent=2)

df_courses = pd.DataFrame(courses)
df_users = pd.DataFrame(users)
df_user_courses = pd.DataFrame(user_courses)

print(f"Количество курсов: {len(df_courses)}")
print(f"Количество пользователей: {len(df_users)}")
print(f"Количество взаимодействий: {len(df_user_courses)}")