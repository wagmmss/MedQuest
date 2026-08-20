import os, glob, re

def check_file(filepath):
    content = open(filepath, 'r', encoding='utf8').read()
    
    # We find all db.execute(..., ...)
    # This regex is a bit simplistic but should catch most standard ones
    matches = re.finditer(r'db\.execute\(\s*(["\'\n\w\s]+?),\s*\((.*?)\)', content, re.DOTALL)
    for m in matches:
        sql = m.group(1)
        args = m.group(2)
        q_count = sql.count('?')
        # Count arguments (rough heuristic: count commas + 1, unless it's empty)
        args = args.strip()
        if args.endswith(','):
            args = args[:-1] # trailing comma for tuples
        
        arg_count = 0 if not args else args.count(',') + 1
        
        if q_count != arg_count:
            print(f"Possible mismatch in {filepath}: SQL has {q_count} '?', args has {arg_count} elements. Args: {args}")

for f in glob.glob('api/*.py'):
    check_file(f)
