import os
import re

def refactor_questions():
    path = r'c:\dev\MedQuest\app\backend\api\questions.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add g import
    if 'from flask import g,' not in content:
        content = content.replace('from flask import Blueprint, jsonify, request', 'from flask import Blueprint, jsonify, request, g')

    # Line 95
    content = content.replace('q.id IN (SELECT question_id FROM attempts)', 'q.id IN (SELECT question_id FROM attempts WHERE user_id = ?)')
    # Need to add g.user_id to params on line 95. Since params is a list in `questions.py` around line 80:
    # Actually, `params` is a list, so I can't just inject it at the end of the query string if the `params` is passed.
    # Wait, the `where` string is built dynamically. 
    # Let's check `api/questions.py` line 95 carefully.
    pass

if __name__ == "__main__":
    refactor_questions()
