from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.api import data_store
from backend.app.api.file_manager import save_raw_data
from backend.ml.training import train_and_save_model
from backend.ml.recommend import recommend_courses_for_user

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

    print(f"Пройденные курсы для {user_id}: {len(result)}")
    print(f"Завершенные курсы с score >= 4: {len([r for r in result if r['score'] >= 4])}")
    print(f"Завершенные курсы с performance >= 60: {len([r for r in result if r['performance'] >= 60])}")
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

    print(f"Непройденные курсы для {user_id}: {len(result)}")
    return {"user_id": user_id, "unpassed_courses": result}

@router.get("/recommendations/{user_id}")
def get_recommendations(user_id: str, top_n: int = 5):
    users = data_store.users

    if not any(user['id'] == user_id for user in users):
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

    recommendations = recommend_courses_for_user(user_id, top_n)
    if not recommendations:
        raise HTTPException(status_code=404, detail=f"Нет данных для рекомендаций для пользователя {user_id}")

    return {"user_id": user_id, "recommendations": recommendations}

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
        existing['performance'] = performance
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

    return {"message": f"Курс {course_id} добавлен для пользователя {user_id} с оценкой {score} и успеваемостью {performance}"}