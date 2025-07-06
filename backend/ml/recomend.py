from joblib import load
from backend.app.api.file_manager import load_raw_data
from backend.ml.get_features import generate_features_for_user

MODELS_DIR = "C:/Users/Hasan/OneDrive/Рабочий стол/recomendation/recomendation/backend/ml/models"

def recommend_courses_for_user(user_id: str, top_k: int = 5):
    model = load(f"{MODELS_DIR}/model.joblib")
    le_user = load(f"{MODELS_DIR}/le_user.joblib")
    mlb = load(f"{MODELS_DIR}/mlb.joblib")
    le_diff = load(f"{MODELS_DIR}/le_diff.joblib")

    courses, users, user_courses = load_raw_data()

    features_df, course_ids = generate_features_for_user(user_id, courses, user_courses, users, le_user, mlb, le_diff)

    if features_df.empty:
        return []

    print("Столбцы в features_df:", features_df.columns.tolist())
    predictions = model.predict(features_df)

    recommendations = list(zip(course_ids, predictions))
    recommendations.sort(key=lambda x: x[1], reverse=True)

    top_courses_ids = [course_id for course_id, _ in recommendations[:top_k]]
    course_dict = {course['id']: course for course in courses}
    top_courses = [
        {
            'id': cid,
            'name': course_dict[cid]['name'],
            'difficulty': course_dict[cid]['difficulty'],
            'tags': course_dict[cid]['tags'],
            'predicted_score': float(predictions[course_ids.index(cid)])
        }
        for cid in top_courses_ids if cid in course_dict
    ]

    return top_courses