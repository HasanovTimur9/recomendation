from fastapi import APIRouter, HTTPException
from backend.app.api import data_store
from backend.ml.get_features import generate_features_for_user
from backend.app.api.file_manager import save_raw_data
from backend.ml.training import train_and_save_model
from pydantic import BaseModel
from joblib import load
import pandas as pd
import random
import os

router = APIRouter()

MODELS_DIR = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/ml/models"

class UserCourseInput(BaseModel):
    user_id: str
    course_id: int
    score: int
    performance: int

class UserCourseDelete(BaseModel):
    user_id: str
    course_id: int

class UserInput(BaseModel):
    user_id: str

def load_models():
    return {
        "model": load(os.path.join(MODELS_DIR, "model.joblib")),
        "le_user": load(os.path.join(MODELS_DIR, "le_user.joblib")),
        "mlb": load(os.path.join(MODELS_DIR, "mlb.joblib")),
        "le_diff": load(os.path.join(MODELS_DIR, "le_diff.joblib"))
    }

@router.get("/courses/passed/{user_id}")
def get_passed_courses(user_id: str):
    courses = data_store.courses
    user_courses = data_store.user_courses
    users = data_store.users

    if not any(user['id'] == user_id for user in users):
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

    passed_courses = [uc for uc in user_courses if uc['user_id'] == user_id and uc['completed']]
    course_dict = {course['id']: course for course in courses}

    result = []
    for uc in passed_courses:
        course_id = uc['course_id']
        if course_id in course_dict:
            course_info = {
                'id': course_dict[course_id]['id'],
                'name': course_dict[course_id]['name'],
                'difficulty': course_dict[course_id]['difficulty'],
                'tags': course_dict[course_id]['tags'],
                'score': uc['score'],
                'performance': uc['performance'],
                'completed': uc['completed']
            }
            result.append(course_info)

    return {"user_id": user_id, "passed_courses": result}


@router.get("/courses/unpassed/{user_id}")
def get_unpassed_courses(user_id: str):
    courses = data_store.courses
    user_courses = data_store.user_courses
    users = data_store.users

    if not any(user['id'] == user_id for user in users):
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

    passed_course_ids = {uc['course_id'] for uc in user_courses if uc['user_id'] == user_id and uc['completed']}
    unpassed_courses = [course for course in courses if course['id'] not in passed_course_ids]

    result = [
        {
            'id': course['id'],
            'name': course['name'],
            'difficulty': course['difficulty'],
            'tags': course['tags'],
            'completed': False,
            'score': None,
            'performance': None
        } for course in unpassed_courses
    ]

    return {"user_id": user_id, "unpassed_courses": result}


@router.get("/recommendations/{user_id}")
def get_recommendations(user_id: str, top_n: int = 5):
    courses = data_store.courses
    user_courses = data_store.user_courses
    users = data_store.users

    if not any(user['id'] == user_id for user in users):
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

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

    # Проверяем пройденные курсы и их успеваемость
    passed_course_ids = {uc['course_id'] for uc in user_courses if uc['user_id'] == user_id and uc['completed']}
    user_completed_courses = [uc for uc in user_courses if uc['user_id'] == user_id and uc['completed']]

    # Фильтруем доступные курсы по зависимости сложности
    available_courses = []
    for category in tag_categories:
        beginner_courses = [c for c in courses if course_categories.get(c['id']) == category and c['difficulty'] == "beginner"]
        intermediate_courses = [c for c in courses if course_categories.get(c['id']) == category and c['difficulty'] == "intermediate"]
        advanced_courses = [c for c in courses if course_categories.get(c['id']) == category and c['difficulty'] == "advanced"]

        completed_beginner = any(
            uc['course_id'] in [c['id'] for c in beginner_courses] and uc['performance'] >= 60
            for uc in user_completed_courses
        )
        completed_intermediate = any(
            uc['course_id'] in [c['id'] for c in intermediate_courses] and uc['performance'] >= 60
            for uc in user_completed_courses
        )

        # Логика доступности (увеличиваем шанс для intermediate до 50%)
        if beginner_courses:
            available_courses.extend([c for c in beginner_courses if c['id'] not in passed_course_ids])
        if completed_beginner and random.random() >= 0.5:  # 50% шанс включения intermediate
            available_courses.extend([c for c in intermediate_courses if c['id'] not in passed_course_ids])
        if completed_beginner and completed_intermediate:
            available_courses.extend([c for c in advanced_courses if c['id'] not in passed_course_ids])

    print(f"Доступные курсы для рекомендаций для {user_id}: {len(available_courses)}")

    # Загружаем модели
    models = load_models()
    model, le_user, mlb, le_diff = models['model'], models['le_user'], models['mlb'], models['le_diff']

    # Генерируем признаки только для доступных курсов
    features_df, course_ids = generate_features_for_user(user_id, available_courses, user_courses, users, le_user, mlb, le_diff)

    if features_df.empty:
        raise HTTPException(status_code=404, detail=f"Нет данных для рекомендаций для пользователя {user_id}")

    print("Столбцы в features_df:", features_df.columns.tolist())
    print("Значения features_df:\n", features_df.head().to_string())
    predictions = model.predict(features_df)

    recommendations = pd.DataFrame({
        'course_id': course_ids,
        'score': predictions
    })

    top_courses = recommendations.sort_values('score', ascending=False).head(top_n)

    course_dict = {course['id']: course for course in available_courses}
    top_courses_info = [
        {
            'id': cid,
            'name': course_dict[cid]['name'],
            'difficulty': course_dict[cid]['difficulty'],
            'tags': course_dict[cid]['tags'],
            'predicted_score': float(top_courses[top_courses['course_id'] == cid]['score'].iloc[0]),
            'performance': None
        }
        for cid in top_courses['course_id'] if cid in course_dict
    ]

    print(f"Рекомендации для {user_id}: {len(top_courses_info)} курсов с предсказанными оценками {[c['predicted_score'] for c in top_courses_info]}")
    return {"user_id": user_id, "recommendations": top_courses_info}


@router.post("/users")
def add_user(payload: UserInput):
    user_id = payload.user_id

    users = data_store.users
    courses = data_store.courses
    user_courses = data_store.user_courses

    if any(user['id'] == user_id for user in users):
        return {"message": f"Пользователь {user_id} уже существует"}

    new_user = {"id": user_id}
    users.append(new_user)
    save_raw_data(courses, users, user_courses)

    if not train_and_save_model(courses, user_courses, users, MODELS_DIR):
        print("Предупреждение: не удалось переобучить модель")

    return {"message": f"Пользователь {user_id} успешно добавлен", "user": new_user}


@router.get("/users/{user_id}")
def get_user_profile(user_id: str):
    users = data_store.users
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")
    return {"user_id": user_id}


@router.post("/user_courses")
def add_user_course(payload: UserCourseInput):
    user_id = payload.user_id
    course_id = payload.course_id
    score = payload.score
    performance = payload.performance

    users = data_store.users
    courses = data_store.courses
    user_courses = data_store.user_courses

    if not any(user['id'] == user_id for user in users):
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

    if not any(course['id'] == course_id for course in courses):
        raise HTTPException(status_code=404, detail=f"Курс с ID {course_id} не найден")

    if not 0 <= score <= 5:
        raise HTTPException(status_code=400, detail="Оценка должна быть от 0 до 5")

    if not 0 <= performance <= 100:
        raise HTTPException(status_code=400, detail="Успеваемость должна быть от 0 до 100")

    existing = next((uc for uc in user_courses if uc['user_id'] == user_id and uc['course_id'] == course_id), None)
    if existing and existing['completed']:
        raise HTTPException(status_code=400, detail=f"Курс уже пройден пользователем")

    if existing:
        existing['completed'] = True
        existing['score'] = score
    else:
        user_courses.append({
            "user_id": user_id,
            "course_id": course_id,
            "completed": True,
            "score": score,
            "performance": performance
        })

    save_raw_data(courses, users, user_courses)

    if not train_and_save_model(courses, user_courses, users, MODELS_DIR):
        print("Предупреждение: не удалось переобучить модель")

    return {"message": f"Курс добавлен"}


@router.delete("/user_courses/{user_id}/{course_id}")
def remove_user_course(user_id: str, course_id: int):
    users = data_store.users
    courses = data_store.courses
    user_courses = data_store.user_courses

    if not any(user['id'] == user_id for user in users):
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

    if not any(course['id'] == course_id for course in courses):
        raise HTTPException(status_code=404, detail=f"Курс {course_id} не найден")

    existing = next((uc for uc in user_courses if uc['user_id'] == user_id and uc['course_id'] == course_id), None)
    if not existing or not existing['completed']:
        raise HTTPException(status_code=404, detail=f"Курс {course_id} не пройден пользователем {user_id}")

    user_courses.remove(existing)
    save_raw_data(courses, users, user_courses)

    if not train_and_save_model(courses, user_courses, users, MODELS_DIR):
        print("Предупреждение: не удалось переобучить модель")

    return {"message": f"Курс {course_id} удален из истории пользователя {user_id}"}


@router.post("/retrain_model")
def retrain_model():
    courses = data_store.courses
    user_courses = data_store.user_courses
    users = data_store.users

    if train_and_save_model(courses, user_courses, users, MODELS_DIR):
        return {"message": "Модель успешно переобучена"}
    else:
        raise HTTPException(status_code=500, detail="Ошибка при переобучении модели")