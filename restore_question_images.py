import sqlite3

backup_path = r'C:\dev\MedQuest\app\backend\backups\medquest_backup_before_170_reclass_20260825_173508.db'
current_path = r'C:\dev\MedQuest\app\backend\medquest.db'

conn_bak = sqlite3.connect(backup_path)
conn_bak.row_factory = sqlite3.Row
cur_bak = conn_bak.cursor()

images_bak = cur_bak.execute("SELECT question_id, file_path, order_index FROM question_images").fetchall()

conn_cur = sqlite3.connect(current_path)
cur_cur = conn_cur.cursor()

restored = 0
for row in images_bak:
    try:
        cur_cur.execute(
            "INSERT INTO question_images (question_id, file_path, order_index) VALUES (?, ?, ?)",
            (row['question_id'], row['file_path'], row['order_index'])
        )
        restored += 1
    except Exception as e:
        print("Error inserting:", e)

conn_cur.commit()
conn_bak.close()
conn_cur.close()

print(f"Restored {restored} rows into question_images.")
