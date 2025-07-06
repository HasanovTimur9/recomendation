import pandas as pd
from fastapi import HTTPException

def generate_features_for_user(user_id: str, courses: list, user_courses: list, users: list, le_user, mlb, le_diff) -> tuple[pd.DataFrame, list]:
    # Получаем ID пройденных курсов
    passed_course_ids = {uc['course_id'] for uc in user_courses if uc['user_id'] == user_id}

    # Фильтруем непройденные курсы
    unseen_courses = [c for c in courses if c['id'] not in passed_course_ids]
    if not unseen_courses:
        return pd.DataFrame(), []

    # Кодируем теги непройденных курсов
    tags_encoded = mlb.transform([course['tags'] for course in unseen_courses])
    df_tags = pd.DataFrame(tags_encoded, columns=mlb.classes_)

    # Формируем базовый DataFrame
    df_base = pd.DataFrame({
        'id': [c['id'] for c in unseen_courses],
        'difficulty': [c['difficulty'] for c in unseen_courses]
    })

    # Кодируем сложность
    try:
        df_base['difficulty_enc'] = le_diff.transform(df_base['difficulty'])
    except ValueError:
        print(f"Ошибка: некоторые значения 'difficulty' не встречались при обучении.")
        return pd.DataFrame(), []

    # Проверяем, известен ли пользователь
    if user_id not in le_user.classes_:
        print(f"Предупреждение: пользователь {user_id} не встречался при обучении модели.")
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

    user_id_encoded = le_user.transform([user_id])[0]

    # Определяем категории тегов
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

    # Определяем категорию для каждого курса
    course_categories = {}
    for course in courses:
        for category, tags in tag_categories.items():
            if any(tag in tags for tag in course['tags']):
                course_categories[course['id']] = category
                break
        else:
            course_categories[course['id']] = None

    # Вычисляем среднюю успеваемость по категориям
    user_completed_courses = [uc for uc in user_courses if uc['user_id'] == user_id and uc['completed']]
    performance_by_category = {}
    for category in tag_categories:
        category_course_ids = [cid for cid, cat in course_categories.items() if cat == category]
        user_performances = [
            uc['performance'] for uc in user_completed_courses
            if uc['course_id'] in category_course_ids
        ]
        performance_by_category[category] = sum(user_performances) / len(user_performances) if user_performances else 0

    # Добавляем нормализованную успеваемость для каждого курса
    df_base['performance_norm'] = df_base['id'].apply(
        lambda cid: performance_by_category.get(course_categories.get(cid, ''), 0) / 100.0
    )

    # Формируем признаки
    df_features = df_tags.copy()
    df_features['user_id_enc'] = user_id_encoded
    df_features['difficulty_enc'] = df_base['difficulty_enc']
    df_features['performance_norm'] = df_base['performance_norm']

    # Проверяем правильность столбцов
    feature_columns = list(mlb.classes_) + ['user_id_enc', 'difficulty_enc', 'performance_norm']
    if set(df_features.columns) != set(feature_columns):
        missing = set(feature_columns) - set(df_features.columns)
        extra = set(df_features.columns) - set(feature_columns)
        raise ValueError(f"Несоответствие столбцов: отсутствуют {missing}, лишние {extra}")

    print("Значения features_df:\n", df_features.head().to_string())
    return df_features, df_base['id'].tolist()