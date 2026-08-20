import sqlite3
import re

def fix_images():
    db = sqlite3.connect('medquest.db')
    db.row_factory = sqlite3.Row
    
    pattern = re.compile(r'imagem (a seguir|abaixo|acima)|seguinte imagem|imagem apresentada|conforme (a )?imagem|figura (a seguir|abaixo|acima)|seguinte figura|radiografia (a seguir|abaixo|acima)|(a seguir|abaixo|acima).{0,20}(imagem|figura|radiografia|tomografia|eletro)|(vide|veja).{0,10}(imagem|figura|exame)', re.IGNORECASE)
    
    images = db.execute('SELECT * FROM question_images').fetchall()
    
    moves = []
    
    for img in images:
        qid = img['question_id']
        q = db.execute('SELECT id, stem, source_file, source_number FROM questions WHERE id = ?', (qid,)).fetchone()
        
        if not q:
            continue
            
        if pattern.search(q['stem']):
            # Current question needs an image, so it's probably correct
            continue
            
        # Current question does NOT need an image (or at least doesn't explicitly mention it).
        # Check next question
        next_q = db.execute('SELECT id, stem FROM questions WHERE source_file = ? AND source_number = ?', (q['source_file'], q['source_number'] + 1)).fetchone()
        
        if next_q and pattern.search(next_q['stem']):
            moves.append((img['id'], q['id'], next_q['id'], img['file_path']))
            continue
            
        # Check previous question
        prev_q = db.execute('SELECT id, stem FROM questions WHERE source_file = ? AND source_number = ?', (q['source_file'], q['source_number'] - 1)).fetchone()
        if prev_q and pattern.search(prev_q['stem']):
            moves.append((img['id'], q['id'], prev_q['id'], img['file_path']))
            
    print(f'Found {len(moves)} images to move.')
    
    cur = db.cursor()
    for m in moves:
        print(f'Moving {m[3]} from Q{m[1]} to Q{m[2]}')
        cur.execute('UPDATE question_images SET question_id = ? WHERE id = ?', (m[2], m[0]))
        
    db.commit()
    print('Done!')

if __name__ == '__main__':
    fix_images()
