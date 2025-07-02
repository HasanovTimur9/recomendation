from fastapi import FastAPI
from backend.app.api import data_store
from backend.app.api.file_manager import load_raw_data, save_raw_data
from backend.app.api.routes import recommendations

COURSES_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/courses.json"
USERS_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/users.json"
USER_COURSES_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/data/raw/user_courses.json"

data_store.courses, data_store.users, data_store.user_courses = load_raw_data()
app = FastAPI()
app.include_router(recommendations.router)
@app.get("/")
async def root():
    return {"message": "Hello, course recommender!"}

@app.on_event("shutdown")
async def save_data_on_exit():
    try:
        save_raw_data(data_store.courses, data_store.users, data_store.user_courses)
        print("Данные успешно сохранены")
    except Exception as e:
        print(f"Ошибка при сохранении данных: {str(e)}")