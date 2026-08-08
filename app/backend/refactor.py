import re
import os

def refactor_stats():
    path = r'c:\dev\MedQuest\app\backend\api\stats.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add g import
    if 'from flask import g,' not in content:
        content = content.replace('from flask import Blueprint, jsonify, request', 'from flask import Blueprint, jsonify, request, g')

    # Replace simple counts
    content = content.replace('"SELECT COUNT(*) n FROM attempts"', '"SELECT COUNT(*) n FROM attempts WHERE user_id = ?", (g.user_id,)')
    content = content.replace('"SELECT COUNT(DISTINCT question_id) n FROM attempts"', '"SELECT COUNT(DISTINCT question_id) n FROM attempts WHERE user_id = ?", (g.user_id,)')
    content = content.replace('"SELECT COUNT(*) n FROM attempts WHERE is_correct = 1"', '"SELECT COUNT(*) n FROM attempts WHERE user_id = ? AND is_correct = 1", (g.user_id,)')
    
    # Replace last_correct query
    content = content.replace('WHERE a1.is_correct = 1', 'WHERE a1.user_id = ? AND a1.is_correct = 1')
    content = content.replace('WHERE a2.question_id = a1.question_id)', 'WHERE a2.user_id = ? AND a2.question_id = a1.question_id)')
    content = content.replace('""").fetchone()["n"]', '""", (g.user_id, g.user_id)).fetchone()["n"]')

    # Replace SRS due
    content = content.replace('next_review_date <= ?"', 'next_review_date <= ? AND user_id = ?"')
    content = content.replace('(now_utc.isoformat(),)', '(now_utc.isoformat(), g.user_id)')

    # Replace last7 / prev7
    content = content.replace('answered_at >= ?"', 'answered_at >= ? AND user_id = ?"')
    content = content.replace('((now_utc - timedelta(days=7)).isoformat(),)', '((now_utc - timedelta(days=7)).isoformat(), g.user_id)')
    
    content = content.replace('answered_at >= ? AND answered_at < ?"', 'answered_at >= ? AND answered_at < ? AND user_id = ?"')
    content = content.replace('((now_utc - timedelta(days=14)).isoformat(), (now_utc - timedelta(days=7)).isoformat())', '((now_utc - timedelta(days=14)).isoformat(), (now_utc - timedelta(days=7)).isoformat(), g.user_id)')

    # Timeline days
    content = content.replace('ORDER BY day DESC"', 'WHERE user_id = ? ORDER BY day DESC", (g.user_id,)')

    # Breakdown queries
    content = content.replace('FROM attempts a JOIN questions q', 'FROM attempts a JOIN questions q') # Wait, I'll replace the WHERE clause
    # actually easier to replace "FROM attempts a JOIN" with "FROM attempts a JOIN questions q ON ... WHERE a.user_id = ?" but there is already a WHERE.
    content = content.replace('WHERE q.', 'WHERE a.user_id = ? AND q.')
    content = content.replace('""").fetchall()', '""", (g.user_id,)).fetchall()')
    # wait, the first breakdown query has '"""' at the end of the query and then ').fetchall()'. 
    # Let's use regex for breakdown
    content = re.sub(r'WHERE q\.([a-zA-Z_]+) IS NOT NULL', r'WHERE a.user_id = ? AND q.\1 IS NOT NULL', content)
    content = re.sub(r'WHERE COALESCE', r'WHERE a.user_id = ? AND COALESCE', content)
    content = re.sub(r'WHERE a\.is_correct = 0', r'WHERE a.user_id = ? AND a.is_correct = 0', content)

    # Some executes might need args appended
    # For _breakdown:
    content = content.replace('""").fetchall()', '""", (g.user_id,)).fetchall()')
    
    # Fix the ones that already had args
    content = content.replace('(min_attempts,)).fetchall()', '(g.user_id, min_attempts)).fetchall()')
    
    # Timeline
    content = content.replace('FROM attempts GROUP BY day', 'FROM attempts WHERE user_id = ? GROUP BY day')
    
    # reset_stats
    content = content.replace('DELETE FROM attempts"', 'DELETE FROM attempts WHERE user_id = ?", (g.user_id,)')
    content = content.replace('DELETE FROM spaced_repetition"', 'DELETE FROM spaced_repetition WHERE user_id = ?", (g.user_id,)')

    # coverage
    content = content.replace('LEFT JOIN attempts a ON a.question_id = q.id', 'LEFT JOIN attempts a ON a.question_id = q.id AND a.user_id = ?')
    content = content.replace('GROUP BY q.area, q.subtema', 'GROUP BY q.area, q.subtema')
    
    # Fix the .fetchall() for coverage (which had no args before)
    content = content.replace('ORDER BY q.area, n_questions DESC\n    """).fetchall()', 'ORDER BY q.area, n_questions DESC\n    """, (g.user_id,)).fetchall()')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    refactor_stats()
