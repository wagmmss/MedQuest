import sqlite3
import re

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

questions = conn.execute("""
    SELECT id, subtema, topic, stem 
    FROM questions 
    WHERE area = 'Pediatria'
""").fetchall()

def classify_ped_question(subtema, topic, stem):
    text = (str(topic) + " " + str(stem)).lower()
    
    # 1. Neonatologia - Sala de parto e Triagem
    if any(re.search(p, text) for p in [r"sala de parto", r"reanimação neonatal", r"clampeamento do cordão", r"\bapgar\b", r"\bvpp\b"]):
        return "Sala de Parto"
    if any(re.search(p, text) for p in [r"alojamento conjunto", r"teste do pezinho", r"teste do olhinho", r"teste do reflexo vermelho", r"teste da orelhinha", r"teste do coraçãozinho", r"triagem neonatal", r"vitamina k", r"profilaxia da conjuntivite", r"credé"]):
        return "Alojamento Conjunto e Testes de Triagem Neonatal"

    # 2. Neonatologia - Doenças específicas
    if any(re.search(p, text) for p in [r"icterícia neonatal", r"hiperbilirrubinemia", r"fototerapia", r"exsanguineotransfusão", r"kernicterus", r"incompatibilidade abo", r"incompatibilidade rh"]):
        return "Período Neonatal: Doenças Hematológicas"
    if any(re.search(p, text) for p in [r"sífilis congênita", r"toxoplasmose congênita", r"citomegalovírus congênito", r"zika congênita", r"sepse neonatal", r"infecção congênita", r"\bstorch\b"]):
        return "Período Neonatal: Doenças Infecciosas"
    if any(re.search(p, text) for p in [r"doença da membrana hialina", r"síndrome do desconforto respiratório", r"taquipneia transitória", r"\bttrn\b", r"síndrome de aspiração meconial", r"\bsam\b"]):
        return "Período Neonatal: Doenças Respiratórias"
    if any(re.search(p, text) for p in [r"hipoglicemia neonatal", r"filho de mãe diabética", r"hipocalcemia neonatal"]):
        return "Período Neonatal: Doenças do Metabolismo"
    if any(re.search(p, text) for p in [r"asfixia perinatal", r"encefalopatia hipóxico-isquêmica", r"hemorragia peri-intraventricular", r"convulsão neonatal"]):
        return "Período Neonatal: Doenças Neurológicas e Sensoriais"

    # 3. Puericultura e Desenvolvimento
    if any(re.search(p, text) for p in [r"baixa estatura", r"puberdade precoce", r"puberdade tardia", r"estirão", r"idade óssea", r"velocidade de crescimento"]):
        return "Distúrbios Estaturais e Puberais"
    if any(re.search(p, text) for p in [r"marcos do desenvolvimento", r"desenvolvimento neuropsicomotor", r"\bdnpm\b", r"escala de denver", r"reflexos primitivos", r"curva de crescimento", r"escore z", r"percentil"]):
        return "Crescimento e Desenvolvimento na Infância e Adolescência"
    if any(re.search(p, text) for p in [r"transtorno do espectro autista", r"\btea\b", r"\btdah\b", r"transtorno de déficit de atenção", r"depressão na adolescência", r"suicídio", r"sono na infância"]):
        return "Avaliação e Transtornos do Comportamento na Infância e Adolescência"
    if any(re.search(p, text) for p in [r"maus-tratos", r"abuso físico", r"negligência", r"violência infantil", r"shaken baby", r"acidentes na infância", r"afogamento", r"queimadura infantil"]):
        return "Segurança e Violência na Infância"

    # 4. Nutrição e Carenciais
    if any(re.search(p, text) for p in [r"anemia ferropriva", r"suplementação de ferro", r"raquitismo", r"vitamina d", r"escorbuto", r"avitaminose", r"carência nutricional"]):
        return "Distúrbios Carenciais"
    if any(re.search(p, text) for p in [r"aleitamento materno", r"leite materno", r"fórmula infantil", r"alimentação complementar", r"desnutrição", r"kwashiorkor", r"marasmo", r"obesidade infantil"]):
        return "Nutrição na Pediatria"

    # 5. Infectologia e Imunização
    if any(re.search(p, text) for p in [r"vacina", r"imunizaç", r"\bpni\b", r"\bbcg\b", r"pentavalente", r"poliomielite", r"\bvip\b", r"\bvop\b", r"pneumocócica", r"meningocócica", r"tríplice viral", r"varicela", r"febre amarela", r"rotavírus"]):
        return "Imunizações"
    if any(re.search(p, text) for p in [r"sarampo", r"rubéola", r"exantema súbito", r"roséola", r"eritema infeccioso", r"parvovírus", r"catapora", r"mão-pé-boca", r"escarlatina", r"kawasaki", r"doença de kawasaki"]):
        return "Doenças Exantemáticas"
    if any(re.search(p, text) for p in [r"ascaridíase", r"giardíase", r"amebíase", r"enterobíase", r"oxiuríase", r"estrongiloidíase", r"ancilostomíase", r"parasitose", r"verminose"]):
        return "Parasitoses"

    # 6. Pneumologia e ORL
    if any(re.search(p, text) for p in [r"asma", r"bronquiolite", r"vírus sincicial", r"\bvsr\b", r"laringite", r"crupe", r"estridor", r"corpo estranho em via aérea"]):
        return "Distúrbios Obstrutivos"
    if any(re.search(p, text) for p in [r"otite média", r"\boma\b", r"sinusite", r"amigdalite", r"faringite", r"faringoamigdalite", r"epiglotite", r"resfriado comum"]):
        return "Nariz, Ouvido e Laringe"

    # 7. Gastro
    if any(re.search(p, text) for p in [r"diarreia aguda", r"gastroenterite", r"desidratação", r"\btro\b", r"plano a", r"plano b", r"plano c", r"doença celíaca", r"alergia à proteína do leite", r"\baplv\b"]):
        return "Síndromes Diarreicas e Disabsortivas"
    if any(re.search(p, text) for p in [r"constipação", r"encoprese", r"fecaloma", r"megacólon congênito", r"hirschsprung"]):
        return "Constipação Intestinal"

    # 8. Nefro / Uro
    if any(re.search(p, text) for p in [r"infecção urinária", r"\bitu\b", r"pielonefrite", r"cistite", r"refluxo vesicoureteral", r"\brvu\b"]):
        return "Infecção do Trato Urinário (ITU)"
    if any(re.search(p, text) for p in [r"síndrome nefrítica", r"\bgnpe\b", r"síndrome nefrótica", r"hematúria", r"proteinúria"]):
        return "Desordens Genéticas e Erros Inatos do Metabolismo"

    # 9. Cardiologia
    if any(re.search(p, text) for p in [r"cardiopatia congênita", r"\bcia\b", r"\bciv\b", r"\bpca\b", r"tetralogia de fallot", r"coarctação de aorta", r"transposição das grandes artérias", r"sopro inocente", r"sopro funcional"]):
        return "Cardiopatias Congênitas"
    if any(re.search(p, text) for p in [r"arritmia", r"parada cardiorrespiratória", r"\bpcr\b", r"\bpals\b", r"taquicardia supraventricular", r"suporte avançado de vida"]):
        return "Arritmias, Síncope e PCR"

    # 10. Emergências / Choque / Neurologia / Imuno
    if any(re.search(p, text) for p in [r"choque séptico", r"sepse pediátrica", r"choque anafilático", r"choque hipovolêmico"]):
        return "Sepse, Choque Séptico e Outros tipos de Choque"
    if any(re.search(p, text) for p in [r"convulsão febril", r"epilepsia", r"estado de mal epiléptico", r"crise convulsiva"]):
        return "Epilepsia e Síndromes Convulsivas"
    if any(re.search(p, text) for p in [r"púrpura de henoch-schönlein", r"vasculite por iga", r"vasculite"]):
        return "Vasculites"
    if any(re.search(p, text) for p in [r"imunodeficiência", r"alergia", r"anafilaxia", r"urticária", r"angioedema"]):
        return "Desordens do Sistema Imune"
    if any(re.search(p, text) for p in [r"erro inato", r"fibrose cística", r"triagem metabólica", r"síndrome de down", r"genética"]):
        return "Desordens Genéticas e Erros Inatos do Metabolismo"

    # Fallback
    sub = str(subtema)
    if "Exantemáticas" in sub: return "Doenças Exantemáticas"
    if "Imuniza" in sub: return "Imunizações"
    if "Parasitoses" in sub: return "Parasitoses"
    if "Icterícia" in sub: return "Período Neonatal: Doenças Hematológicas"
    if "Crescimento" in sub: return "Crescimento e Desenvolvimento na Infância e Adolescência"
    if "Neonatologia" in sub: return "Sala de Parto"
    if "Diarreia" in sub: return "Síndromes Diarreicas e Disabsortivas"
    if "Maus-Tratos" in sub: return "Segurança e Violência na Infância"
    if "Triagem" in sub: return "Alojamento Conjunto e Testes de Triagem Neonatal"
    if "Nefro" in sub: return "Infecção do Trato Urinário (ITU)"
    if "Desnutrição" in sub: return "Nutrição na Pediatria"
    if "Cardiopatias" in sub: return "Cardiopatias Congênitas"
    if "Emergências" in sub: return "Epilepsia e Síndromes Convulsivas"
    if "Infecções Respiratórias" in sub: return "Distúrbios Obstrutivos"
    
    return "Crescimento e Desenvolvimento na Infância e Adolescência"

updates = []
for q in questions:
    new_sub = classify_ped_question(q["subtema"], q["topic"], q["stem"])
    updates.append((new_sub, q["id"]))

print(f"Applying {len(updates)} subtema updates to medquest.db for Pediatria...")
conn.executemany("UPDATE questions SET subtema = ? WHERE id = ?", updates)
conn.commit()
print("All Pediatria questions updated in local medquest.db!")
