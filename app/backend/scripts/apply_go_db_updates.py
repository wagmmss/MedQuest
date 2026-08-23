import sqlite3
import re

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

questions = conn.execute("""
    SELECT id, subtema, topic, stem 
    FROM questions 
    WHERE area LIKE '%Ginecologia%' OR area LIKE '%Obstetr%'
""").fetchall()

def classify_question(subtema, topic, stem):
    text = (str(topic) + " " + str(stem)).lower()
    
    # 1. Mama
    if any(re.search(p, text) for p in [r"\bmama\b", r"\bmamas\b", r"mamári", r"birads", r"bi-rads", r"mastolog", r"fibroadenoma"]):
        if any(w in text for w in ["câncer", "carcinoma", "malign", "ductal", "lobular", "paget", "linfonodo sentinela"]):
            return "Tumores Malignos da Mama"
        return "Doenças Benignas da Mama"

    # 2. Sangramentos Obstétricos
    if any(re.search(p, text) for p in [r"descolamento prematuro", r"\bdpp\b", r"placenta prévia", r"placenta de inserção", r"rotura de vasa", r"rotura uterina", r"segunda metade"]):
        return "Sangramento da Segunda Metade da Gestação"
    if any(re.search(p, text) for p in [r"abort", r"prenhez ectópica", r"gravidez ectópica", r"ectópica", r"mola hidatiforme", r"doença trofoblástica", r"primeira metade"]):
        return "Sangramento da Primeira Metade da Gestação"

    # 3. Colo Uterino
    if any(re.search(p, text) for p in [r"\bcolo\b", r"cérv", r"cervic", r"hpv", r"nic\b", r"nic\s*i", r"nic\s*ii", r"nic\s*iii", r"citopatolog", r"papanicolaou", r"colposcop", r"cervical", r"lesão intraepitelial"]):
        if any(w in text for w in ["estadiamento", "invasor", "wertheim", "braquiterapia", "quimioterapia", "carcinoma de colo"]):
            return "Tumores do colo uterino"
        return "Rastreamento do Câncer de Colo Uterino"

    # 4. Vulva / Vagina / Sexualidade / Fístula
    if "fístula" in text or "fistula" in text:
        return "Fístulas"
    if any(re.search(p, text) for p in [r"disfunção sexual", r"disfunções sexuais", r"vaginismo", r"dispareunia"]):
        return "Disfunções sexuais"
    if any(re.search(p, text) for p in [r"violência sexual", r"estupro", r"abuso sexual"]):
        return "Doença Inflamatória Pélvica e Violência Sexual"
    if any(re.search(p, text) for p in [r"sexualidade", r"resposta sexual", r"orientação sexual", r"identidade de gênero"]):
        return "Conceitos em sexualidade"
    if any(re.search(p, text) for p in [r"úlcera genital", r"úlceras genitais", r"cancro", r"sífilis", r"herpes genital", r"herpes simples", r"donovanose", r"linfogranuloma"]):
        return "Úlceras genitais"
    if any(re.search(p, text) for p in [r"candidíase", r"vaginose", r"tricomoníase", r"corrimento", r"vulvovaginite"]):
        return "Vulvovaginites"
    if any(re.search(p, text) for p in [r"\bvulva\b", r"\bvagina\b", r"bartolinite", r"líquen", r"bartholin", r"\bniv\b"]):
        return "Patologias da Vulva e Vagina"

    # 5. DIP
    if any(re.search(p, text) for p in [r"\bdip\b", r"doença inflamatória pélvica", r"salpingite", r"abscesso tubo-ovariano"]):
        return "Doença Inflamatória Pélvica e Violência Sexual"

    # 6. Urogineco / Anatomia
    if any(re.search(p, text) for p in [r"incontinência", r"prolapso", r"cistocele", r"retocele", r"urodinâmica", r"bexiga hiperativa", r"sling"]):
        return "Incontinência Urinária e Prolapsos de Órgãos Pélvicos"
    if any(re.search(p, text) for p in [r"anatomia pélvica", r"assoalho pélvico", r"fáscia endopélvica"]):
        return "Anatomia Pélvica"

    # 7. Endométrio / Corpo Uterino / Mioma / Endometriose
    if any(re.search(p, text) for p in [r"mioma", r"leiomioma", r"sangramento uterino anormal", r"\bsua\b", r"palm-coein", r"pólipo endometrial", r"adenomiose"]):
        return "PALM-COEIN"
    if any(re.search(p, text) for p in [r"endometriose", r"dor pélvica crônica", r"dismenorreia"]):
        return "Dor pélvica crônica"
    if any(re.search(p, text) for p in [r"câncer de endométrio", r"carcinoma de endométrio", r"hiperplasia endometrial", r"espessamento endometrial", r"endométrio"]):
        return "Doenças do Corpo Uterino e Endométrio"
    if any(re.search(p, text) for p in [r"câncer de ovário", r"tumor ovariano", r"cisto de ovário", r"massa anexial", r"teratoma", r"cistoadenoma"]):
        return "Tumores dos Ovários"

    # 8. Gineco Endócrino
    if any(re.search(p, text) for p in [r"climatério", r"menopausa", r"fogacho", r"terapia hormonal", r"\bth\b"]):
        return "Climatério"
    if any(re.search(p, text) for p in [r"anticoncepção", r"contracepção", r"\bdiu\b", r"laqueadura", r"vasectomia", r"anticoncepcional", r"pílula combinada"]):
        return "Contracepção"
    if any(re.search(p, text) for p in [r"amenorreia", r"amenorréia", r"\bsop\b", r"ovários policísticos", r"hirsutismo"]):
        return "Amenorreias e掌Síndrome dos Ovários Policísticos".replace("掌", "")
    if any(re.search(p, text) for p in [r"infertilidade", r"espermograma", r"histerossalpingografia", r"reprodução assistida"]):
        return "Infertilidade conjugal"
    if any(re.search(p, text) for p in [r"ciclo menstrual", r"fase lútea", r"fase folicular", r"ovulação", r"eixo hipotálamo"]):
        return "Ciclo Menstrual"

    # 9. Obstetrícia - Doenças na Gestação
    if any(re.search(p, text) for p in [r"hipertens", r"pré-eclâmpsia", r"eclâmpsia", r"hellp", r"sulfato de magnésio"]):
        return "Síndromes Hipertensivas da Gestação"
    if any(re.search(p, text) for p in [r"diabete", r"glicemia de jejum", r"totg", r"\bdmg\b"]):
        return "Diabetes mellitus na gravidez"
    if any(re.search(p, text) for p in [r"\bhiv\b", r"hepatite", r"sífilis congênita", r"toxoplasmose", r"citomegalovírus", r"zika", r"infecção congênita", r"storch"]):
        return "Hepatites virais, HIV/AIDS e outras infecções na gestação"
    if any(re.search(p, text) for p in [r"trombofilia", r"anemia na gestação", r"isoimunização", r"coombs", r"rh negativo", r"cardiopatia na gravidez"]):
        return "Outras doenças na gestação"

    # 10. Parto / Prematuridade / Sofrimento Fetal
    if any(re.search(p, text) for p in [r"parto prematuro", r"\btpp\b", r"tocólise", r"corticoide antenatal", r"colo curto"]):
        return "Trabalho de parto prematuro"
    if any(re.search(p, text) for p in [r"bolsa rota", r"rotura prematura", r"\bprom\b", r"\brpmo\b", r"corioamnionite", r"infecção ovular"]):
        return "Rotura Prematura de Membranas Ovulares e Infecção Ovular"
    if any(re.search(p, text) for p in [r"cardiotocografia", r"perfil biofísico fetal", r"dopplerfluxometria", r"doppler fetal", r"sofrimento fetal", r"\bdip\s*ii\b", r"\bdip\s*iii\b", r"mecônio"]):
        return "Sofrimento Fetal"
    if any(re.search(p, text) for p in [r"medicina fetal", r"malformação fetal", r"translucência nucal", r"gemelar", r"gemelaridade", r"stff", r"restrição de crescimento", r"\brcf\b", r"\bciur\b"]):
        return "Medicina Fetal"
    if any(re.search(p, text) for p in [r"estática fetal", r"bacia", r"mecanismo de parto", r"insinuação", r"variedade de posição", r"\bpelve\b", r"diâmetros da bacia"]):
        return "Estática fetal, Pelve e Mecanismo de Parto"
    if any(re.search(p, text) for p in [r"morte materna", r"óbito materno", r"mortalidade materna", r"razão de mortalidade materna"]):
        return "Morte materna"
    if any(re.search(p, text) for p in [r"puerpério", r"hemorragia pós-parto", r"atonia uterina", r"loquiação", r"infecção puerperal", r"endometrite pós-parto"]):
        return "Puerpério"
    if any(re.search(p, text) for p in [r"partograma", r"trabalho de parto", r"cesárea", r"cesariana", r"fórcipe", r"vácuo-extrator", r"episiotomia", r"indução do parto", r"bishop"]):
        return "Assistência ao Parto"
    if any(re.search(p, text) for p in [r"pré-natal", r"pre-natal", r"consulta pré-natal", r"suplementação", r"vacinação na gestante", r"idade gestacional", r"data da última menstruação", r"\bdum\b", r"regra de naegele"]):
        return "Pré-Natal"

    # Fallback
    sub = str(subtema)
    if "Hemorragias da Primeira" in sub: return "Sangramento da Primeira Metade da Gestação"
    if "Hemorragias da Segunda" in sub: return "Sangramento da Segunda Metade da Gestação"
    if "Síndromes Hipertensivas" in sub: return "Síndromes Hipertensivas da Gestação"
    if "Diabetes" in sub: return "Diabetes mellitus na gravidez"
    if "Pré-Natal" in sub: return "Pré-Natal"
    if "Parto" in sub: return "Assistência ao Parto"
    if "Ciclo" in sub: return "Ciclo Menstrual"
    if "Anticoncep" in sub: return "Contracepção"
    if "Climat" in sub: return "Climatério"
    if "Amenorreia" in sub: return "Amenorreias e Síndrome dos Ovários Policísticos"
    if "Colo" in sub: return "Rastreamento do Câncer de Colo Uterino"
    if "Mama" in sub or "Mastologia" in sub: return "Doenças Benignas da Mama"
    if "Vulvovaginites" in sub: return "Vulvovaginites"
    if "Endométrio" in sub: return "Doenças do Corpo Uterino e Endométrio"
    if "Vitalidade" in sub: return "Sofrimento Fetal"
    if "Sangramento Uterino" in sub: return "PALM-COEIN"
    
    return "Pré-Natal"

updates = []
for q in questions:
    new_sub = classify_question(q["subtema"], q["topic"], q["stem"])
    updates.append((new_sub, q["id"]))

print(f"Applying {len(updates)} subtema updates to medquest.db...")
conn.executemany("UPDATE questions SET subtema = ? WHERE id = ?", updates)
conn.commit()
print("All Ginecologia e Obstetrícia questions updated in local medquest.db!")
