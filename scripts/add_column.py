import sqlite3

# 连接到数据库
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

try:
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(recognition_record)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'annotated_image_path' not in column_names:
        # 添加字段
        cursor.execute('ALTER TABLE recognition_record ADD COLUMN annotated_image_path VARCHAR(255)')
        conn.commit()
        print('Column annotated_image_path added successfully')
    else:
        print('Column annotated_image_path already exists')

except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()