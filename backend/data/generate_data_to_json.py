import random
import pandas as pd
import json

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
    return tags

num_courses = 150
courses = []
for i in range(1, num_courses + 1):
    category = random.choice(list(tag_categories.keys()))
    num_tags = random.randint(1, 3)
    tags = get_logical_tags(category, num_tags)
    if category == "databases" and "sql" not in tags:
        tags.append("sql")
    if category == "web-development" and "html" not in tags and random.random() < 0.5:
        tags.append("html")
    difficulty = random.choice(difficulties)
    courses.append({"id": i, "difficulty": difficulty, "tags": tags})

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
    selected_courses = random.sample(courses, num_interactions)
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

df_courses = pd.DataFrame(courses)
df_users = pd.DataFrame(users)
df_user_courses = pd.DataFrame(user_courses)

with open("courses.json", "w", encoding="utf-8") as f:
    json.dump(courses, f, ensure_ascii=False, indent=2)

with open("users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, ensure_ascii=False, indent=2)

with open("user_courses.json", "w", encoding="utf-8") as f:
    json.dump(user_courses, f, ensure_ascii=False, indent=2)

print(f"Количество курсов: {len(df_courses)}")
print(f"Количество пользователей: {len(df_users)}")
print(f"Количество взаимодействий: {len(df_user_courses)}")