import sqlite3
import json

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

# Get all GO questions
questions = conn.execute("""
    SELECT id, subtema, topic, stem 
    FROM questions 
    WHERE area LIKE '%Ginecologia%' OR area LIKE '%Obstetr%'
""").fetchall()

print(f"Total GO questions to map: {len(questions)}")

# Let's see mapping rules based on topic and stem
# 37 target modules:
# 1. Tumores do colo uterino
# 2. Pré-Natal
# 3. Rastreamento do Câncer de Colo Uterino
# 4. Doenças do Corpo Uterino e Endométrio
# 5. Diabetes mellitus na gravidez
# 6. Outras doenças na gestação
# 7. Síndromes Hipertensivas da Gestação
# 8. Hepatites virais, HIV/AIDS e outras infecções na gestação
# 9. Ciclo Menstrual
# 10. Contracepção
# 11. Climatério
# 12. Amenorreias e Síndrome dos Ovários Policísticos
# 13. Anatomia Pélvica
# 14. Dor pélvica crônica
# 15. Doença Inflamatória Pélvica e Violência Sexual
# 16. Vulvovaginites
# 17. Infertilidade conjugal
# 18. Doenças Benignas da Mama
# 19. Tumores Malignos da Mama
# 20. Medicina Fetal
# 21. Tumores dos Ovários
# 22. Estática fetal, Pelve e Mecanismo de Parto
# 23. Assistência ao Parto
# 24. Rotura Prematura de Membranas Ovulares e Infecção Ovular
# 25. Trabalho de parto prematuro
# 26. Puerpério
# 27. Sangramento da Primeira Metade da Gestação
# 28. Sangramento da Segunda Metade da Gestação
# 29. PALM-COEIN
# 30. Sofrimento Fetal
# 31. Úlceras genitais
# 32. Incontinência Urinária e Prolapsos de Órgãos Pélvicos
# 33. Patologias da Vulva e Vagina
# 34. Conceitos em sexualidade
# 35. Disfunções sexuais
# 36. Fístulas
# 37. Morte materna

def classify_question(subtema, topic, stem):
    text = (str(topic) + " " + str(stem)).lower()
    
    # 1. Mama
    if "mama" in text or "mamári" in text or "birads" in text or "bi-rads" in text or "mastolog" in text or "fibroadenoma" in text:
        if any(w in text for w in ["câncer", "carcinoma", "malign", "ductal", "lobular", "paget", "linfonodo sentinela"]):
            return "Tumores Malignos da Mama"
        return "Doenças Benignas da Mama"
        
    # 2. Colo Uterino
    if "colo" in text or "cérv" in text or "cervic" in text or "hpv" in text or "nic " in text or "nic i" in text or "citopatolog" in text or "papanicolaou" in text or "colposcop" in text:
        if any(w in text for w in ["estadiamento", "invasor", "wertheim", "braquiterapia", "quimioterapia"]):
            return "Tumores do colo uterino"
        return "Rastreamento do Câncer de Colo Uterino"
        
    # 3. Vulva / Vagina / Sexualidade / Fístula
    if "fístula" in text or "fistula" in text:
        return "Fístulas"
    if "sexual" in text or "libido" in text or "vaginismo" in text or "dispareunia" in text or "orgasm" in text:
        if any(w in text for w in ["disfunção", "disfuncoes"]):
            return "Disfunções sexuais"
        if "violência" in text or "estupro" in text:
            return "Doença Inflamatória Pélvica e Violência Sexual"
        return "Conceitos em sexualidade"
    if "úlcera" in text or "cancro" in text or "sífilis" in text or "herpes" in text or "donovanose" in text or "linfogranuloma" in text:
        return "Úlceras genitais"
    if "candidíase" in text or "vaginose" in text or "tricomoníase" in text or "corrimento" in text or "vulvovaginite" in text:
        return "Vulvovaginites"
    if "vulva" in text or "vagina" in text or "bartolinite" in text or "líquen" in text or "barrtholin" in text or "niv" in text:
        return "Patologias da Vulva e Vagina"
        
    # 4. DIP
    if "dip" in text or "doença inflamatória pélvica" in text or "salpingite" in text or "abscesso tubo-ovariano" in text:
        return "Doença Inflamatória Pélvica e Violência Sexual"

    # 5. Urogineco / Anatomia
    if "incontinência" in text or "prolapso" in text or "cistocele" in text or "retocele" in text or "urodinâmica" in text or "bexiga hiperativa" in text or "sling" in text:
        return "Incontinência Urinária e Prolapsos de Órgãos Pélvicos"
    if "anatomia" in text or "ligamento" in text or "assoalho pélvico" in text:
        return "Anatomia Pélvica"

    # 6. Endométrio / Corpo Uterino / Mioma / Endometriose
    if "mioma" in text or "sangramento uterino anormal" in text or "sua" in text or "palm-coein" in text or "pólipo" in text or "adenomiose" in text:
        return "PALM-COEIN"
    if "endometriose" in text or "dor pélvica" in text:
        return "Dor pélvica crônica"
    if "endométrio" in text or "hiperplasia endometrial" in text or "espessamento endometrial" in text:
        return "Doenças do Corpo Uterino e Endométrio"
    if "ovário" in text or "ovariano" in text or "massa anexial" in text or "cisto ovariano" in text:
        if "policístico" in text or "sop" in text:
            return "Amenorreias e Síndrome dos Ovários Policísticos"
        return "Tumores dos Ovários"

    # 7. Gineco Endócrino
    if "climatério" in text or "menopausa" in text or "fogachos" in text or "terapia hormonal" in text or "th" in text:
        return "Climatério"
    if "anticoncepção" in text or "contracepção" in text or "diu" in text or "laqueadura" in text or "vasectomia" in text or "método anticoncepcional" in text:
        return "Contracepção"
    if "amenorreia" in text or "amenorréia" in text or "sop" in text or "ovários policísticos" in text or "hirsutismo" in text:
        return "Amenorreias e Síndrome dos Ovários Policísticos"
    if "infertilidade" in text or "espermograma" in text or "histerossalpingografia" in text or "reprodução assistida" in text:
        return "Infertilidade conjugal"
    if "ciclo menstrual" in text or "fase lútea" in text or "fase folicular" in text or "ovulação" in text:
        return "Ciclo Menstrual"

    # 8. Obstetrícia - Doenças na Gestação
    if "hipertens" in text or "pré-eclâmpsia" in text or "eclâmpsia" in text or "hellp" in text or "sulfato de magnésio" in text:
        return "Síndromes Hipertensivas da Gestação"
    if "diabete" in text or "glicemia de jejum" in text or "totg" in text or "dmg" in text:
        return "Diabetes mellitus na gravidez"
    if "hiv" in text or "hepatite" in text or "sífilis congênita" in text or "toxoplasmose" in text or "citomegalovírus" in text or "zika" in text or "infecção na gestação" in text:
        return "Hepatites virais, HIV/AIDS e outras infecções na gestação"
    if "trombofilia" in text or "anemia na gestação" in text or "isoimunização" in text or "coombs" in text or "rh negativo" in text or "cardiopatia na gravidez" in text or "doença na gestação" in text:
        return "Outras doenças na gestação"

    # 9. Sangramentos na Gestação
    if "abort" in text or "ectópica" in text or "prenhez ectópica" in text or "mola hidatiforme" in text or "doença trofoblástica" in text or "primeira metade" in text:
        return "Sangramento da Primeira Metade da Gestação"
    if "descolamento prematuro" in text or "dpp" in text or "placenta prévia" in text or "rotura de vasa prévia" in text or "rotura uterina" in text or "segunda metade" in text:
        return "Sangramento da Segunda Metade da Gestação"

    # 10. Parto / Prematuridade / Sofrimento Fetal
    if "prematur" in text or "trabalho de parto prematuro" in text or "tpp" in text or "tocólise" in text or "corticoide" in text:
        return "Trabalho de parto prematuro"
    if "bolsa rota" in text or "rotura prematura" in text or "prom" in text or "corioamnionite" in text or "infecção ovular" in text:
        return "Rotura Prematura de Membranas Ovulares e Infecção Ovular"
    if "cardiotocografia" in text or "perfil biofísico" in text or "doppler" in text or "sofrimento fetal" in text or "dips" in text or "mecônio" in text:
        return "Sofrimento Fetal"
    if "medicina fetal" in text or "malformação" in text or "translucência nucal" in text or "gemelar" in text or "gemelaridade" in text or "stff" in text:
        return "Medicina Fetal"
    if "estática fetal" in text or "bacia" in text or "mecanismo de parto" in text or "insinuação" in text or "variedade de posição" in text or "pelve" in text:
        return "Estática fetal, Pelve e Mecanismo de Parto"
    if "partograma" in text or "parto" in text or "cesárea" in text or "fórcipe" in text or "vácuo" in text or "episiotomia" in text or "indução do parto" in text:
        return "Assistência ao Parto"
    if "morte materna" in text or "óbito materno" in text or "mortalidade materna" in text:
        return "Morte materna"
    if "puerpério" in text or "hemorragia pós-parto" in text or "atonia uterina" in text or "loquiação" in text or "infecção puerperal" in text or "endometrite pós-parto" in text:
        return "Puerpério"
    if "pré-natal" in text or "pre-natal" in text or "consulta pré-natal" in text or "suplementação" in text or "vacinação na gestante" in text:
        return "Pré-Natal"

    # Fallback to subtema mapping
    sub = str(subtema)
    if "Hemorragias da Primeira" in sub: return "Sangramento da Primeira Metade da Gestação"
    if "Hemorragias da Segunda" in sub: return "Sangramento da Segunda Metade da Gestação"
    if "SÃ­ndromes Hipertensivas" in sub or "Síndromes Hipertensivas" in sub: return "Síndromes Hipertensivas da Gestação"
    if "Diabetes" in sub: return "Diabetes mellitus na gravidez"
    if "Pré-Natal" in sub or "PrÃ©-Natal" in sub: return "Pré-Natal"
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

# Test classification
counts = {}
for q in questions:
    target = classify_question(q["subtema"], q["topic"], q["stem"])
    counts[target] = counts.get(target, 0) + 1

print("\nDistribution across 37 Medway Modules:")
for mod_name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
    print(f" - {mod_name}: {count} questions")

print(f"\nTotal mapped: {sum(counts.values())} across {len(counts)} modules")
