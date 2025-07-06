import pandas as pd
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from joblib import dump
from fastapi import HTTPException

def prepare_data(courses, user_courses, users):
    df_courses = pd.DataFrame(courses)
    df_user_course = pd.DataFrame(user_courses)

    if df_courses.empty or df_user_course.empty:
        raise ValueError("Один из входных наборов данных пуст")

    # Определяем interested как completed и score >= 4
    df_user_course['interested'] = df_user_course.apply(
        lambda row: int(row['completed'] and row['score'] >= 4), axis=1
    )

    # Кодируем теги курсов
    mlb = MultiLabelBinarizer()
    tags_encoded = mlb.fit_transform(df_courses['tags'])
    df_tags = pd.DataFrame(tags_encoded, columns=mlb.classes_, index=df_courses.index)

    # Кодируем сложность
    le_diff = LabelEncoder()
    df_courses['difficulty_enc'] = le_diff.fit_transform(df_courses['difficulty'])

    # Отладочная информация
    print("Уникальные теги:", mlb.classes_.tolist())
    print("Уникальные сложности:", df_courses['difficulty'].unique().tolist())
    df_courses['tags_tuple'] = df_courses['tags'].apply(lambda x: tuple(sorted(x)))
    print("Количество уникальных комбинаций (теги, сложность):",
          len(df_courses[['tags_tuple', 'difficulty']].drop_duplicates()))

    # Объединяем данные о курсах
    df_courses_full = pd.concat([df_courses[['id', 'difficulty_enc']], df_tags], axis=1)

    # Кодируем user_id
    le_user = LabelEncoder()
    df_user_course['user_id_enc'] = le_user.fit_transform(df_user_course['user_id'])

    # Объединяем данные
    df_merged = df_user_course.merge(df_courses_full, left_on='course_id', right_on='id', how='inner')

    # Нормализуем performance (0–100) в [0, 1]
    df_merged['performance_norm'] = df_user_course['performance'] / 100.0

    # Формируем признаки
    feature_columns = list(mlb.classes_) + ['user_id_enc', 'difficulty_enc', 'performance_norm']
    missing_columns = [col for col in feature_columns if col not in df_merged.columns]
    if missing_columns:
        raise KeyError(f"Следующие столбцы отсутствуют в df_merged: {missing_columns}")

    X = df_merged[feature_columns]
    y = df_merged['interested']

    # Отладочная информация
    print("Обучающие столбцы (X):", X.columns.tolist())
    print("Распределение y:", y.value_counts().to_dict())
    print("Пример X:\n", X.head().to_string())

    return X, y, le_user, mlb, le_diff, df_courses_full

def train_model(X, y):
    model = RandomForestRegressor(n_estimators=100, random_state=1)
    model.fit(X, y)
    return model

def train_and_save_model(courses, user_courses, users, models_dir):
    try:
        X, y, le_user, mlb, le_diff, df_courses_full = prepare_data(courses, user_courses, users)
        model = train_model(X, y)

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