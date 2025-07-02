from sklearn.ensemble import RandomForestRegressor
from joblib import dump
import os


def prepare_data(courses, user_courses, users):
    import pandas as pd
    from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder

    df_courses = pd.DataFrame(courses)
    df_user_course = pd.DataFrame(user_courses)
    df_users = pd.DataFrame(users)

    if df_courses.empty or df_user_course.empty or df_users.empty:
        raise ValueError("Некорректные входные данные")

    df_user_course['interested'] = df_user_course.apply(
        lambda row: int(row['completed'] and row['score'] >= 4), axis=1
    )

    all_tags = set()
    for tags in df_courses['tags']:
        all_tags.update(tags)
    for interests in df_users['interests']:
        all_tags.update(interests)

    if not all_tags:
        raise ValueError("Некорректные тэги")

    mlb = MultiLabelBinarizer()
    mlb.fit([list(all_tags)])

    tags_encoded = mlb.transform(df_courses['tags'])
    df_tags = pd.DataFrame(tags_encoded, columns=mlb.classes_, index=df_courses.index)

    interests_encoded = mlb.transform(df_users['interests'])
    df_interests = pd.DataFrame(interests_encoded, columns=mlb.classes_, index=df_users['id'])

    le_diff = LabelEncoder()
    df_courses['difficulty_enc'] = le_diff.fit_transform(df_courses['difficulty'])

    df_courses_full = pd.concat([df_courses[['id', 'difficulty_enc']], df_tags], axis=1)

    le_user = LabelEncoder()
    df_user_course['user_id_enc'] = le_user.fit_transform(df_user_course['user_id'])

    df_merged = df_user_course.merge(df_courses_full, left_on='course_id', right_on='id', how='inner')
    df_merged = df_merged.merge(df_interests, left_on='user_id', right_index=True, how='left')

    for col in mlb.classes_:
        if col not in df_merged.columns:
            df_merged[col] = 0

    feature_columns = list(mlb.classes_) + ['user_id_enc', 'difficulty_enc']
    missing_columns = [col for col in feature_columns if col not in df_merged.columns]
    if missing_columns:
        raise KeyError(f"Следующие столбцы отсутствуют в df_merged: {missing_columns}")

    x = df_merged[feature_columns]
    y = df_merged['interested']

    return x, y, le_user, mlb, le_diff, df_courses_full

def train_model(x, y):
    model = RandomForestRegressor(n_estimators=100, random_state=1)
    model.fit(x, y)
    return model

def train_and_save_model(courses, user_courses, users, models_dir):
    try:
        x, y, le_user, mlb, le_diff, df_courses_full = prepare_data(courses, user_courses, users)
        model = train_model(x, y)

        os.makedirs(models_dir, exist_ok=True)
        dump(model, f"{models_dir}/model.joblib")
        dump(le_user, f"{models_dir}/le_user.joblib")
        dump(mlb, f"{models_dir}/mlb.joblib")
        dump(le_diff, f"{models_dir}/le_diff.joblib")
        print("Модель успешно переобучена и сохранена")
        return True
    except Exception as e:
        print(f"Ошибка при переобучении модели: {str(e)}")
        return False