import pandas as pd
from fastapi import HTTPException

def generate_features_for_user(user_id: str, courses: list, user_courses: list, users: list, le_user, mlb, le_diff) -> tuple[pd.DataFrame, list]:
    passed_course_ids = {uc['course_id'] for uc in user_courses if uc['user_id'] == user_id}

    unseen_courses = [c for c in courses if c['id'] not in passed_course_ids]

    if not unseen_courses:
        return pd.DataFrame(), []

    tags_encoded = mlb.transform([course['tags'] for course in unseen_courses])
    df_tags = pd.DataFrame(tags_encoded, columns=mlb.classes_)

    df_base = pd.DataFrame({
        'id': [c['id'] for c in unseen_courses],
        'difficulty': [c['difficulty'] for c in unseen_courses]
    })

    try:
        df_base['difficulty_enc'] = le_diff.transform(df_base['difficulty'])
    except ValueError:
        print(f"Ошибка: некоторые значения 'difficulty' не встречались при обучении.")
        return pd.DataFrame(), []

    if user_id not in le_user.classes_:
        print(f"Предупреждение: пользователь {user_id} не встречался при обучении модели.")
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

    user_id_encoded = le_user.transform([user_id])[0]

    df_features = df_tags.copy()
    df_features['user_id_enc'] = user_id_encoded
    df_features['difficulty_enc'] = df_base['difficulty_enc']

    feature_columns = list(mlb.classes_) + ['user_id_enc', 'difficulty_enc']
    df_features = df_features[feature_columns]

    if set(df_features.columns) != set(feature_columns):
        missing = set(feature_columns) - set(df_features.columns)
        extra = set(df_features.columns) - set(feature_columns)
        raise ValueError(f"Несоответствие столбцов: отсутствуют {missing}, лишние {extra}")

    print("Значения features_df:\n", df_features.head().to_string())
    return df_features, df_base['id'].tolist()