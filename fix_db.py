import mysql.connector

conn = mysql.connector.connect(
    host='localhost', user='root', password='', database='pneumonia_db'
)
cursor = conn.cursor()

# Fix model_used ENUM to allow any model name
cursor.execute(
    "ALTER TABLE prediction_logs MODIFY model_used VARCHAR(50) NOT NULL DEFAULT 'resnet50'"
)
conn.commit()
print('DB schema updated: model_used is now VARCHAR(50)')

# Show tables to confirm DB is healthy
cursor.execute("SHOW TABLES")
print("Tables:", cursor.fetchall())

conn.close()
