import json
import re

data = json.load(open('medway_topics.json', encoding='utf-8'))
for item in data:
    if "Tumores do colo uterino" in item:
        names = re.findall(r'"name":"([^"]+)"', item)
        print(f'Found {len(names)} themes in Medway HAR:')
        for i, name in enumerate(names):
            print(f'{i+1}. {name}')
        break
