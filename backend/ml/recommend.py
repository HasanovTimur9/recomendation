import pandas as pd
import random
from joblib import load
from backend.ml.get_features import generate_features_for_user

MODELS_DIR = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/ml/models"
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


def load_raw_data():
    from backend.app.api.file_manager import load_raw_data
    return load_raw_data()


def recommend_courses_for_user(user_id: str, top_k: int = 5):
    model = load(f"{MODELS_DIR}/model.joblib")
    le_user = load(f"{MODELS_DIR}/le_user.joblib")
    mlb = load(f"{MODELS_DIR}/mlb.joblib")
    le_diff = load(f"{MODELS_DIR}/le_diff.joblib")

    courses, users, user_courses = load_raw_data()

    # Проверяем существование пользователя
    if not any(user['id'] == user_id for user in users):
        return []

    # Определяем категорию для каждого курса
    course_categories = {}
    for course in courses:
        for category, tags in tag_categories.items():
            if any(tag in tags for tag in course['tags']):
                course_categories[course['id']] = category
                break
        else:
            course_categories[course['id']] = None

    # Проверяем пройденные курсы
    passed_course_ids = {uc['course_id'] for uc in user_courses if uc['user_id'] == user_id and uc['completed']}
    user_completed_courses = [uc for uc in user_courses if uc['user_id'] == user_id and uc['completed']]

    # Фильтруем доступные курсы по зависимости сложности
    available_courses = []
    category_performance = {}
    for category in tag_categories:
        beginner_courses = [c for c in courses if
                            course_categories.get(c['id']) == category and c['difficulty'] == "beginner"]
        intermediate_courses = [c for c in courses if
                                course_categories.get(c['id']) == category and c['difficulty'] == "intermediate"]
        advanced_courses = [c for c in courses if
                            course_categories.get(c['id']) == category and c['difficulty'] == "advanced"]

        # Проверяем успеваемость по beginner курсам
        beginner_performances = [
            uc['performance'] for uc in user_completed_courses
            if uc['course_id'] in [c['id'] for c in beginner_courses]
        ]
        category_performance[category] = sum(beginner_performances) / len(
            beginner_performances) if beginner_performances else 0

        completed_beginner_success = any(
            uc['course_id'] in [c['id'] for c in beginner_courses] and uc['performance'] >= 60
            for uc in user_completed_courses
        )
        completed_intermediate_success = any(
            uc['course_id'] in [c['id'] for c in intermediate_courses] and uc['performance'] >= 60
            for uc in user_completed_courses
        )
        completed_beginner_poor = any(
            uc['course_id'] in [c['id'] for c in beginner_courses] and uc['performance'] < 60
            for uc in user_completed_courses
        )

        # Логика доступности
        if beginner_courses:
            if completed_beginner_poor:
                # Добавляем другие beginner курсы с похожими тегами
                poor_beginner_courses = [
                    uc for uc in user_completed_courses
                    if uc['course_id'] in [c['id'] for c in beginner_courses] and uc['performance'] < 60
                ]
                for uc in poor_beginner_courses:
                    poor_course_id = uc['course_id']
                    poor_course_tags = next(c['tags'] for c in beginner_courses if c['id'] == poor_course_id)
                    similar_beginner_courses = [
                        c for c in beginner_courses
                        if c['id'] not in passed_course_ids and
                           len(set(c['tags']).intersection(set(poor_course_tags))) >= 1
                    ]
                    available_courses.extend(similar_beginner_courses)
            else:
                # Добавляем все beginner курсы, если нет плохо пройденных
                available_courses.extend([c for c in beginner_courses if c['id'] not in passed_course_ids])

        if (completed_beginner_success or random.random() < 0.9) and intermediate_courses:
            available_courses.extend([c for c in intermediate_courses if c['id'] not in passed_course_ids])
        if completed_beginner_success and completed_intermediate_success and advanced_courses:
            available_courses.extend([c for c in advanced_courses if c['id'] not in passed_course_ids])

    # Удаляем дубликаты
    available_courses = list({c['id']: c for c in available_courses}.values())

    print(f"Доступные курсы для рекомендаций для {user_id}: {len(available_courses)}")
    print(f"Категории доступных курсов: {set(course_categories.get(c['id']) for c in available_courses)}")
    print(f"Средняя успеваемость по категориям (beginner): {category_performance}")

    # Генерируем признаки только для доступных курсов
    features_df, course_ids = generate_features_for_user(user_id, available_courses, user_courses, users, le_user, mlb,
                                                         le_diff)

    if features_df.empty:
        return []

    print("Столбцы в features_df:", features_df.columns.tolist())
    print("Значения features_df (первые 5 строк):\n", features_df.head().to_string())
    predictions = model.predict(features_df)

    recommendations = list(zip(course_ids, predictions))
    recommendations.sort(key=lambda x: x[1], reverse=True)

    top_courses_ids = [course_id for course_id, _ in recommendations[:top_k]]
    course_dict = {course['id']: course for course in available_courses}
    top_courses = [
        {
            'id': cid,
            'name': course_dict[cid]['name'],
            'difficulty': course_dict[cid]['difficulty'],
            'tags': course_dict[cid]['tags'],
            'predicted_score': float(predictions[course_ids.index(cid)]),
            'performance': None
        }
        for cid in top_courses_ids if cid in course_dict
    ]

    print(
        f"Рекомендации для {user_id}: {len(top_courses)} курсов с предсказанными оценками {[c['predicted_score'] for c in top_courses]}")
    return top_courses