import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root@123",
    database="caretrack"
)

cursor = connection.cursor()

cursor.execute("""
    ALTER TABLE medical_records
    ADD COLUMN extracted_text LONGTEXT
""")

connection.commit()

print("Database updated successfully.")

cursor.close()
connection.close()