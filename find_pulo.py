import os
import re

directory = "c:/dev/MedQuest"

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith((".py", ".json", ".md", ".ts", ".tsx", ".html")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue

            if re.search(r"regra de ouro", content, re.IGNORECASE):
                print(f"File with 'regra de ouro': {path}")
            
            # also find medcof image links
            images = re.findall(r'!\[.*?\]\((.*?)\)', content)
            html_images = re.findall(r'<img.*?src=[\"\'](.*?)[\"\']', content)
            
            for img in images + html_images:
                if "medcof" in img.lower():
                    print(f"Image link with medcof: {img} in {path}")
