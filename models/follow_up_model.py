import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

MODEL_PATH = "models/follow_up_model.pkl"


def prepare_features(checkins):

    rows = []

    for patient_id, patient_checkins in checkins.items():

        if len(patient_checkins) < 3:
            continue

        # Use groups of 3 check-ins as training examples
        for i in range(len(patient_checkins) - 2):

            window = patient_checkins[i:i + 3]

            df = pd.DataFrame(window)

            rows.append({
                "patient_id": patient_id,

                "avg_mood": df["mood"].mean(),

                "avg_pain": df["pain_level"].mean(),

                "avg_sleep": df["sleep_hours"].mean(),

                "high_pain_count": (
                    df["pain_level"] >= 5
                ).sum(),

                "low_mood_count": (
                    df["mood"] <= 2
                ).sum(),

                "low_sleep_count": (
                    df["sleep_hours"] < 6
                ).sum(),

                "missed_medication_count": (
                    df["medication_taken"] == False
                ).sum()
            })

    return pd.DataFrame(rows)


def create_attention_label(df):

    df["review_attention"] = (
        (
            (df["avg_pain"] >= 5)
            |
            (df["high_pain_count"] >= 2)
            |
            (df["low_mood_count"] >= 2)
            |
            (df["low_sleep_count"] >= 2)
        )
        .astype(int)
    )

    return df


def train_model(df):

    feature_columns = [
        "avg_mood",
        "avg_pain",
        "avg_sleep",
        "high_pain_count",
        "low_mood_count",
        "low_sleep_count",
        "missed_medication_count"
    ]

    X = df[feature_columns]

    y = df["review_attention"]

    print("\nTraining examples:", len(df))

    print("\nClass distribution:")
    print(y.value_counts())

    if len(df) < 10:

        print(
            "\nNot enough training examples."
        )

        return

    if y.nunique() < 2:

        print(
            "\nOnly one class is present."
        )

        print(
            "Add more varied check-in data."
        )

        return

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    print("\nModel evaluation:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    joblib.dump(
        model,
        MODEL_PATH
    )

    print(
        f"\nModel saved successfully: {MODEL_PATH}"
    )


def load_model():

    try:

        return joblib.load(
            MODEL_PATH
        )

    except FileNotFoundError:

        return None