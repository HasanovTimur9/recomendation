from fastapi import APIRouter, HTTPException
from backend.app.api import data_store
from backend.ml.get_features import generate_features_for_user
from backend.app.api.file_manager import save_raw_data
from backend.ml.training import train_and_save_model
from pydantic import BaseModel
from joblib import load
import pandas as pd
import os

router = APIRouter()

MODELS_DIR = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/ml/models"

class UserCourseInput(BaseModel):
    user_id: str
    course_id: int
    score: int

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
            'score': None
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

    models = load_models()
    model, le_user, mlb, le_diff = models['model'], models['le_user'], models['mlb'], models['le_diff']

    features_df, course_ids = generate_features_for_user(user_id, courses, user_courses, users, le_user, mlb, le_diff)

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

    course_dict = {course['id']: course for course in courses}
    top_courses_info = [
        {
            'id': cid,
            'name': course_dict[cid]['name'],
            'difficulty': course_dict[cid]['difficulty'],
            'tags': course_dict[cid]['tags'],
            'predicted_score': float(top_courses[top_courses['course_id'] == cid]['score'].iloc[0])
        }
        for cid in top_courses['course_id'] if cid in course_dict
    ]

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

    users = data_store.users
    courses = data_store.courses
    user_courses = data_store.user_courses

    if not any(user['id'] == user_id for user in users):
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

    if not any(course['id'] == course_id for course in courses):
        raise HTTPException(status_code=404, detail=f"Курс {course_id} не найден")

    if not 0 <= score <= 5:
        raise HTTPException(status_code=400, detail="Оценка должна быть от 0 до 5")

    existing = next((uc for uc in user_courses if uc['user_id'] == user_id and uc['course_id'] == course_id), None)
    if existing and existing['completed']:
        raise HTTPException(status_code=400, detail=f"Курс {course_id} уже пройден пользователем {user_id}")

    if existing:
        existing['completed'] = True
        existing['score'] = score
    else:
        user_courses.append({
            "user_id": user_id,
            "course_id": course_id,
            "completed": True,
            "score": score
        })

    save_raw_data(courses, users, user_courses)

    if not train_and_save_model(courses, user_courses, users, MODELS_DIR):
        print("Предупреждение: не удалось переобучить модель")

    return {"message": f"Курс {course_id} добавлен для пользователя {user_id} с оценкой {score}"}


@router.delete("/user_courses/{user_id}/{course_id}")
def remove_user_course(payload: UserCourseDelete):
    user_id = payload.user_id
    course_id = payload.course_id

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