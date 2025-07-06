from backend.data.generate_data_to_json import user_courses
from backend.ml.training import prepare_data, train_model
from backend.app.api import data_store
from backend.app.api import file_manager
from joblib import dump
import os

MODELS_PATH = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/ml/models"

courses, users, user_courses = file_manager.load_raw_data()

#courses = data_store.courses
#users = data_store.users
#user_courses = data_store.user_courses

model_dir = MODELS_PATH
os.makedirs(model_dir, exist_ok=True)

X, y, le_user, mlb, le_diff, df_courses_full = prepare_data(courses, user_courses, users)
model = train_model(X, y)

dump(model, f"{model_dir}/model.joblib")
dump(le_user, f"{model_dir}/le_user.joblib")
dump(mlb, f"{model_dir}/mlb.joblib")
dump(le_diff, f"{model_dir}/le_diff.joblib")