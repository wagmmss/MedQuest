import sqlite3

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

# Check the 54 NULL questions
null_qs = conn.execute("SELECT id, stem, topic FROM questions WHERE area IS NULL OR subtema IS NULL").fetchall()
print(f"--- 54 NULL Questions Sample ---")
for q in null_qs[:5]:
    print(f"ID {q['id']}: Topic: {q['topic']} | Stem: {q['stem'][:80]}...")

# Check Rastreamento do Câncer de Colo Uterino (454 questions)
go_colo = conn.execute("""
    SELECT id, stem, topic 
    FROM questions 
    WHERE subtema = 'Rastreamento do Câncer de Colo Uterino'
""").fetchall()

print(f"\n--- Rastreamento do Câncer de Colo Uterino (Total: {len(go_colo)}) ---")
# Let's see what distinct topics/words are in these 454 questions
keywords = {}
for q in go_colo:
    text = (str(q["topic"]) + " " + str(q["stem"])).lower()
    for w in ["parto", "cesárea", "vulvovaginite", "candidíase", "mioma", "endometriose", "climatério", "anticoncep", "sangramento", "prenhez", "abort", "feto", "bcf", "cardiotoco"]:
        if w in text:
            keywords[w] = keywords.get(w, 0) + 1

print("Found non-colo keywords inside 'Rastreamento do Câncer de Colo Uterino':")
for k, v in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
    print(f" - Contains '{k}': {v} questions")
