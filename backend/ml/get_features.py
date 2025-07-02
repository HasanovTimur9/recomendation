import pandas as pd
from fastapi import HTTPException


def generate_features_for_user(user_id: str, courses: list, user_courses: list, users: list, le_user, mlb, le_diff) -> \
tuple[pd.DataFrame, list]:
    # Множество ID курсов, которые пользователь уже прошел
    passed_course_ids = {uc['course_id'] for uc in user_courses if uc['user_id'] == user_id}

    # Фильтрация непройденных курсов
    unseen_courses = [c for c in courses if c['id'] not in passed_course_ids]

    if not unseen_courses:
        return pd.DataFrame(), []

    # Кодирование тегов курсов
    tags_encoded = mlb.transform([course['tags'] for course in unseen_courses])
    df_tags = pd.DataFrame(tags_encoded, columns=mlb.classes_)

    # Создание базового DataFrame
    df_base = pd.DataFrame({
        'id': [c['id'] for c in unseen_courses],
        'difficulty': [c['difficulty'] for c in unseen_courses]
    })

    # Кодирование сложности
    try:
        df_base['difficulty_enc'] = le_diff.transform(df_base['difficulty'])
    except ValueError:
        print(f"Ошибка: некоторые значения 'difficulty' не встречались при обучении.")
        return pd.DataFrame(), []

    # Кодирование user_id
    if user_id not in le_user.classes_:
        print(f"Предупреждение: пользователь {user_id} не встречался при обучении модели.")
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

    user_id_encoded = le_user.transform([user_id])[0]

    # Кодирование интересов пользователя
    df_users = pd.DataFrame(users)
    if user_id not in df_users['id'].values:
        print(f"Предупреждение: пользователь {user_id} не найден в данных users.")
        raise HTTPException(status_code=404, detail=f"Пользователь {user_id} не найден")

    user_interests = df_users[df_users['id'] == user_id]['interests'].iloc[0]
    interests_encoded = mlb.transform([user_interests])[0]
    df_interests = pd.DataFrame([interests_encoded], columns=mlb.classes_)

    # Создание DataFrame с признаками
    # Объединяем теги курсов и интересы пользователя (суммируем бинарные значения)
    df_features = df_tags.copy()
    for col in mlb.classes_:
        df_features[col] = df_tags[col] + df_interests[col].reindex(df_tags.index, method='ffill').astype(int)

    # Добавляем user_id_enc и difficulty_enc
    df_features['user_id_enc'] = user_id_encoded
    df_features['difficulty_enc'] = df_base['difficulty_enc']

    # Явно задаем порядок столбцов, как в обучении
    feature_columns = list(mlb.classes_) + ['user_id_enc', 'difficulty_enc']
    df_features = df_features[feature_columns]

    # Проверка на наличие всех столбцов
    if set(df_features.columns) != set(feature_columns):
        missing = set(feature_columns) - set(df_features.columns)
        extra = set(df_features.columns) - set(feature_columns)
        raise ValueError(f"Несоответствие столбцов: отсутствуют {missing}, лишние {extra}")

    return df_features, df_base['id'].tolist()