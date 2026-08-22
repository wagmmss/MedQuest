import re
import json

TS_FILE = r'C:\dev\MedQuest\app\frontend\src\lib\plannerData.ts'
with open(TS_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Separate JSON from the trailing code
match = re.search(r'(export const plannerData = \[.*?\];)(.*)', content, flags=re.DOTALL)
if match:
    json_part = match.group(1)
    trailing_code = match.group(2)
    
    # We can just use string replacement on json_part
    # Replace `"dbSubtemas": [...]` with the contents of `"details": [...]`
    # Actually, a simple regex is safer: replace dbSubtemas list with details list
    
    def repl(m):
        return f'"dbSubtemas": {m.group(1)},\n        "details": {m.group(1)}'
        
    # find "dbSubtemas": [...], then "details": [...]
    # We'll just replace the whole block
    new_json = re.sub(r'"dbSubtemas":\s*\[.*?\],\s*"details":\s*(\[.*?\])', repl, json_part, flags=re.DOTALL)
    
    with open(TS_FILE, 'w', encoding='utf-8') as f:
        f.write(new_json + trailing_code)
    print("Success! dbSubtemas replaced with details.")
else:
    print("Regex failed to match.")
