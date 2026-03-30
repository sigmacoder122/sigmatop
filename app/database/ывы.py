import sqlite3

# Подключаемся к твоей базе данных
# Убедись, что название файла совпадает с твоим (обычно db.sqlite3)
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

try:
    # Добавляем новую колонку aging_days типа INTEGER со значением по умолчанию 0
    cursor.execute("ALTER TABLE items ADD COLUMN aging_days INTEGER DEFAULT 0;")
    conn.commit()
    print("✅ Колонка aging_days успешно добавлена! Данные сохранены.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Ошибка (возможно, колонка уже существует): {e}")
finally:
    conn.close()