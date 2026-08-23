import sqlite3
import re

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

# Check candidate questions for the zero-question topics
zero_keywords = {
    "Vasculites (Clínica)": r"vasculite|granulomatose de wegener|churg-strauss|panarterite|arterite de takayasu",
    "Intoxicações e Peçonhentos (Clínica)": r"intoxicação|botróp|crotál|escorpi|lachesis|paracetamol|organofosforad",
    "Neurológicas e Fraqueza (Clínica)": r"guillain-barré|miastenia gravis|esclerose múltipla|fraqueza muscular|motoneurônio|ela\b",
    "Pulmonares Intersticiais (Clínica)": r"fibrose pulmonar|sarcoidose|pneumonite por hipersensibilidade|interstici",
    "Síndrome Disfágica (Cirurgia)": r"disfagia|megaesôfago|acalásia|esôfago de barrett",
    "Síndrome Dispéptica (Cirurgia)": r"dispepsia|úlcera péptica|h\. pylori|gastrite",
    "Fraturas Ósseas (Cirurgia)": r"fratura|rádio|fêmur|tíbia|úmero|clavícula|consolidação",
    "Luxações / Ligamentares (Cirurgia)": r"luxação|entorse|ligamento cruzado|lca|manguito rotador|menisco",
    "Tendinites / Bursites (Cirurgia)": r"tendinite|bursite|fasceíte|epicondilite|tenossinovite",
    "TRM (Cirurgia)": r"raquimedular|\btrm\b|fratura de coluna|choque neurogênico",
    "Morte Materna (G.O.)": r"morte materna|óbito materno|razão de mortalidade materna",
    "Fístulas (G.O.)": r"fístula vesicovaginal|fístula retovaginal|fístula obstétrica",
    "Disfunções Sexuais (G.O.)": r"disfunção sexual|vaginismo|dispareunia|anorgasmia|desejo sexual hipoativo",
    "Patologias da Vulva (G.O.)": r"líquen escleroso|neoplasia intraepitelial vulvar|\bniv\b|carcinoma de vulva|glândula de bartholin|bartholin",
    "Anatomia Pélvica (G.O.)": r"ligamento largo|ligamento redondo|artéria uterina|assoalho pélvico|anatomia pélvica",
    "Metabolismo Neonatal (Pediatria)": r"hipoglicemia neonatal|filho de mãe diabética|hipocalcemia neonatal"
}

print("Searching for candidate questions in the bank for zero-question topics:")
for name, pattern in zero_keywords.items():
    cnt = 0
    for r in conn.execute("SELECT id, stem, topic, subtema FROM questions").fetchall():
        text = (str(r["topic"]) + " " + str(r["stem"]) + " " + str(r["subtema"])).lower()
        if re.search(pattern, text):
            cnt += 1
    print(f" - {name}: {cnt} candidate questions found in DB")
