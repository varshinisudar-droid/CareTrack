import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from database.db_connection import get_connection
from models.follow_up_model import (
    prepare_features,
    create_attention_label,
    train_model
)


connection = get_connection()

cursor = connection.cursor(
    dictionary=True
)

cursor.execute("""
    SELECT
        patient_id,
        checkin_date,
        mood,
        pain_level,
        sleep_hours,
        medication_taken
    FROM health_checkins
    ORDER BY patient_id, checkin_date
""")

rows = cursor.fetchall()

cursor.close()
connection.close()


checkins = {}

for row in rows:

    patient_id = row["patient_id"]

    if patient_id not in checkins:
        checkins[patient_id] = []

    checkins[patient_id].append(row)


df = prepare_features(
    checkins
)

df = create_attention_label(
    df
)

print("\nTraining data:")
print(df)

train_model(df)