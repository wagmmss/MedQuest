import extract
path = r'C:\dev\MedQuest\USP 2020 a 2023.pdf'
records, anchors = extract.parse_pdf(path, 'USP')
candidates = extract.collect_image_candidates(path)

for qnum in [148, 149, 150, 151]:
    anchor = next((a for a in anchors if a[2] == qnum), None)
    if anchor:
        print(f"Q{qnum} anchor: page {anchor[0]}, top {anchor[1]}")

for c in candidates:
    if c["page"] in [93, 94, 95]:
        print(f"Image: page {c['page']}, top {c['top']}")
