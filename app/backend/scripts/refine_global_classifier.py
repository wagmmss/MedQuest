import sqlite3
import re
import json

conn = sqlite3.connect("app/backend/medquest.db")
conn.row_factory = sqlite3.Row

# Load 170 canonical modules
with open("canonical_modules_170.json", "r", encoding="utf-8") as f:
    canonical_170 = json.load(f)

questions = conn.execute("SELECT id, area, subtema, topic, stem FROM questions").fetchall()

def classify_question_refined(q):
    raw_area = str(q["area"] or "")
    topic = str(q["topic"] or "")
    stem = str(q["stem"] or "")
    sub = str(q["subtema"] or "")
    
    text = (topic + " " + stem + " " + sub).lower()
    
    # 0. Determine Area
    target_area = None
    if "Pediatria" in raw_area or "criança" in text[:50] or "lactente" in text[:50] or "recém-nascido" in text[:50] or "pediatria" in topic.lower():
        target_area = "Pediatria"
    elif "Ginecologia" in raw_area or "obstetrícia" in text[:50] or "gestante" in text[:50] or "primigesta" in text[:50] or "multípara" in text[:50] or "colo uterino" in text[:50] or "ginecologia" in topic.lower():
        target_area = "Ginecologia e Obstetrícia"
    elif "Preventiva" in raw_area or "epidemiologia" in topic.lower() or "saúde coletiva" in topic.lower() or "sus" in text[:50]:
        target_area = "Medicina Preventiva"
    elif "Cirurgia" in raw_area or "cirurgia" in topic.lower() or "trauma" in topic.lower() or "fratura" in topic.lower():
        target_area = "Cirurgia"
    elif "Clínica" in raw_area or "nica" in raw_area or "clínica médica" in topic.lower():
        target_area = "Clínica Médica"
    else:
        if any(w in text for w in ["gestante", "útero", "parto", "colo uterino", "vulvovaginite", "mama", "ovário", "puerpério"]):
            target_area = "Ginecologia e Obstetrícia"
        elif any(w in text for w in ["lactente", "prematuro", "pediatria", "vacinação", "pni", "denver", "apgar"]):
            target_area = "Pediatria"
        elif any(w in text for w in ["estudo de coorte", "ensaio clínico", "sensibilidade", "especificidade", "sus", "leavell"]):
            target_area = "Medicina Preventiva"
        elif any(w in text for w in ["laparotomia", "apendicite", "hérnia", "trauma", "fratura", "colecistite"]):
            target_area = "Cirurgia"
        else:
            target_area = "Clínica Médica"

    # =====================================================================
    # 1. PEDIATRIA
    # =====================================================================
    if target_area == "Pediatria":
        if any(re.search(p, text) for p in [r"sala de parto", r"reanimação neonatal", r"clampeamento", r"\bapgar\b", r"\bvpp\b"]):
            return ("Pediatria", "Sala de Parto")
        if any(re.search(p, text) for p in [r"alojamento conjunto", r"teste do pezinho", r"teste do olhinho", r"teste do reflexo vermelho", r"teste da orelhinha", r"teste do coraçãozinho", r"vitamina k", r"credé"]):
            return ("Pediatria", "Alojamento Conjunto e Testes de Triagem Neonatal")
        if any(re.search(p, text) for p in [r"icterícia neonatal", r"hiperbilirrubinemia", r"fototerapia", r"exsanguineotransfusão", r"kernicterus", r"incompatibilidade abo", r"incompatibilidade rh"]):
            return ("Pediatria", "Período Neonatal: Doenças Hematológicas")
        if any(re.search(p, text) for p in [r"sífilis congênita", r"toxoplasmose congênita", r"citomegalovírus", r"zika", r"sepse neonatal", r"\bstorch\b"]):
            return ("Pediatria", "Período Neonatal: Doenças Infecciosas")
        if any(re.search(p, text) for p in [r"membrana hialina", r"desconforto respiratório", r"taquipneia transitória", r"\bttrn\b", r"aspiração meconial", r"\bsam\b", r"surfactante"]):
            return ("Pediatria", "Período Neonatal: Doenças Respiratórias")
        if any(re.search(p, text) for p in [r"hipoglicemia neonatal", r"filho de mãe diabética", r"hipocalcemia neonatal"]):
            return ("Pediatria", "Período Neonatal: Doenças do Metabolismo")
        if any(re.search(p, text) for p in [r"asfixia perinatal", r"encefalopatia hipóxico", r"hemorragia peri-intraventricular", r"convulsão neonatal"]):
            return ("Pediatria", "Período Neonatal: Doenças Neurológicas e Sensoriais")
        if any(re.search(p, text) for p in [r"baixa estatura", r"puberdade precoce", r"puberdade tardia", r"estirão", r"idade óssea"]):
            return ("Pediatria", "Distúrbios Estaturais e Puberais")
        if any(re.search(p, text) for p in [r"marcos do desenvolvimento", r"dnpm", r"escala de denver", r"reflexos primitivos", r"curva de crescimento", r"escore z", r"percentil"]):
            return ("Pediatria", "Crescimento e Desenvolvimento na Infância e Adolescência")
        if any(re.search(p, text) for p in [r"autismo", r"\btea\b", r"\btdah\b", r"transtorno de déficit", r"depressão na adolescência", r"sono na infância"]):
            return ("Pediatria", "Avaliação e Transtornos do Comportamento na Infância e Adolescência")
        if any(re.search(p, text) for p in [r"maus-tratos", r"abuso físico", r"negligência", r"violência infantil", r"shaken baby", r"afogamento", r"acidentes na infância"]):
            return ("Pediatria", "Segurança e Violência na Infância")
        if any(re.search(p, text) for p in [r"anemia ferropriva", r"suplementação de ferro", r"raquitismo", r"vitamina d", r"escorbuto", r"avitaminose"]):
            return ("Pediatria", "Distúrbios Carenciais")
        if any(re.search(p, text) for p in [r"aleitamento materno", r"leite materno", r"fórmula infantil", r"alimentação complementar", r"desnutrição", r"kwashiorkor", r"marasmo", r"obesidade infantil"]):
            return ("Pediatria", "Nutrição na Pediatria")
        if any(re.search(p, text) for p in [r"vacina", r"imunizaç", r"\bpni\b", r"\bbcg\b", r"pentavalente", r"poliomielite", r"\bvip\b", r"\bvop\b", r"tríplice viral", r"varicela", r"febre amarela"]):
            return ("Pediatria", "Imunizações")
        if any(re.search(p, text) for p in [r"sarampo", r"rubéola", r"exantema súbito", r"roséola", r"eritema infeccioso", r"parvovírus", r"catapora", r"mão-pé-boca", r"escarlatina", r"kawasaki"]):
            return ("Pediatria", "Doenças Exantemáticas")
        if any(re.search(p, text) for p in [r"ascarid", r"giárdia", r"amebíase", r"enterobíase", r"oxiuríase", r"estrongiloidíase", r"ancilóstomo", r"parasitose", r"verminose"]):
            return ("Pediatria", "Parasitoses")
        if any(re.search(p, text) for p in [r"asma", r"bronquiolite", r"vírus sincicial", r"\bvsr\b", r"laringite", r"crupe", r"estridor", r"corpo estranho"]):
            return ("Pediatria", "Distúrbios Obstrutivos")
        if any(re.search(p, text) for p in [r"otite média", r"\boma\b", r"sinusite", r"amigdalite", r"faringite", r"resfriado comum"]):
            return ("Pediatria", "Nariz, Ouvido e Laringe")
        if any(re.search(p, text) for p in [r"diarreia aguda", r"gastroenterite", r"desidratação", r"\btro\b", r"plano a", r"plano b", r"plano c", r"doença celíaca", r"aplv"]):
            return ("Pediatria", "Síndromes Diarreicas e Disabsortivas")
        if any(re.search(p, text) for p in [r"constipação", r"encoprese", r"fecaloma", r"hirschsprung"]):
            return ("Pediatria", "Constipação Intestinal")
        if any(re.search(p, text) for p in [r"infecção urinária", r"\bitu\b", r"pielonefrite", r"cistite", r"refluxo vesicoureteral"]):
            return ("Pediatria", "Infecção do Trato Urinário (ITU)")
        if any(re.search(p, text) for p in [r"cardiopatia congênita", r"\bcia\b", r"\bciv\b", r"\bpca\b", r"fallot", r"coarctação"]):
            return ("Pediatria", "Cardiopatias Congênitas")
        if any(re.search(p, text) for p in [r"arritmia", r"parada cardiorrespiratória", r"\bpcr\b", r"\bpals\b", r"taquicardia supraventricular"]):
            return ("Pediatria", "Arritmias, Síncope e PCR")
        if any(re.search(p, text) for p in [r"choque séptico", r"sepse pediátrica", r"choque anafilático"]):
            return ("Pediatria", "Sepse, Choque Séptico e Outros tipos de Choque")
        if any(re.search(p, text) for p in [r"convulsão febril", r"epilepsia", r"estado de mal", r"crise convulsiva"]):
            return ("Pediatria", "Epilepsia e Síndromes Convulsivas")
        if any(re.search(p, text) for p in [r"henoch-schönlein", r"vasculite"]):
            return ("Pediatria", "Vasculites")
        if any(re.search(p, text) for p in [r"imunodeficiência", r"alergia", r"anafilaxia"]):
            return ("Pediatria", "Desordens do Sistema Imune")
        if any(re.search(p, text) for p in [r"erro inato", r"fibrose cística", r"síndrome de down", r"genética", r"gnpe", r"nefrótica"]):
            return ("Pediatria", "Desordens Genéticas e Erros Inatos do Metabolismo")
        return ("Pediatria", "Crescimento e Desenvolvimento na Infância e Adolescência")

    # =====================================================================
    # 2. MEDICINA PREVENTIVA
    # =====================================================================
    if target_area == "Medicina Preventiva":
        if any(re.search(p, text) for p in [r"ética médica", r"bioética", r"código de ética", r"sigilo", r"segredo", r"autonomia", r"atestado", r"declaração de óbito", r"prontuário"]):
            return ("Medicina Preventiva", "Ética médica, Bioética e Documentação")
        if any(re.search(p, text) for p in [r"sensibilidade", r"especificidade", r"\bvpp\b", r"\bvpn\b", r"razão de verossimilhança", r"curva roc", r"ponto de corte", r"acurácia"]):
            return ("Medicina Preventiva", "Estatística de Testes Diagnósticos")
        if any(re.search(p, text) for p in [r"risco relativo", r"\brr\b", r"odds ratio", r"\bor\b", r"razão de chances", r"razão de prevalência", r"risco atribuível", r"\bnnt\b", r"\bnnh\b", r"teste de hipótese", r"erro tipo i", r"valor de p", r"intervalo de confiança"]):
            return ("Medicina Preventiva", "Estudos Epidemiológicos (Análise Estatística e Aplicação)")
        if any(re.search(p, text) for p in [r"estudo de coorte", r"caso-controle", r"ensaio clínico", r"estudo transversal", r"estudo ecológico", r"meta-análise", r"randomização"]):
            return ("Medicina Preventiva", "Estudos Epidemiológicos (Classificação)")
        if any(re.search(p, text) for p in [r"transição demográfica", r"taxa de fecundidade", r"pirâmide etária", r"envelhecimento populacional", r"esperança de vida"]):
            return ("Medicina Preventiva", "Perfis e Indicadores demográficos")
        if any(re.search(p, text) for p in [r"taxa de mortalidade", r"coeficiente de mortalidade", r"mortalidade infantil", r"mortalidade materna", r"letalidade", r"incidência", r"prevalência", r"daly"]):
            return ("Medicina Preventiva", "Indicadores de Morbimortalidade")
        if any(re.search(p, text) for p in [r"prevenção primária", r"prevenção secundária", r"prevenção terciária", r"prevenção quaternária", r"prevenção primordial", r"rastreamento", r"screening", r"sobrediagnóstico"]):
            return ("Medicina Preventiva", "Níveis de Prevenção")
        if any(re.search(p, text) for p in [r"saúde do trabalhador", r"doença ocupacional", r"acidente de trabalho", r"\bcat\b", r"ler/dort", r"pneumoconiose", r"silicose", r"benzenismo"]):
            return ("Medicina Preventiva", "Vigilância em Saúde do Trabalhador")
        if any(re.search(p, text) for p in [r"notificação compulsória", r"sinan", r"lista nacional de notificação", r"notificação imediata"]):
            return ("Medicina Preventiva", "Notificação")
        if any(re.search(p, text) for p in [r"epidemia", r"endemia", r"pandemia", r"surto", r"curva epidêmica", r"\br0\b", r"imunidade de rebanho", r"canal endêmico"]):
            return ("Medicina Preventiva", "Epidemias, Endemias e Pandemias")
        if any(re.search(p, text) for p in [r"atenção primária", r"\baps\b", r"estratégia saúde da família", r"\besf\b", r"starfield", r"longitudinalidade", r"genograma", r"ecomapa"]):
            return ("Medicina Preventiva", "Atenção Primária à Saúde")
        if any(re.search(p, text) for p in [r"inamps", r"caixas de aposentadoria", r"caps", r"iaps", r"reforma sanitária", r"8ª conferência", r"movimento sanitário"]):
            return ("Medicina Preventiva", "Aspectos Históricos do SUS")
        if any(re.search(p, text) for p in [r"lei 8080", r"lei 8142", r"nob-sus", r"decreto 7508", r"financiamento do sus", r"controle social", r"conselho de saúde", r"princípios do sus"]):
            return ("Medicina Preventiva", "A Evolução do SUS")
        return ("Medicina Preventiva", "Atenção Primária à Saúde")

    # =====================================================================
    # 3. GINECOLOGIA E OBSTETRÍCIA
    # =====================================================================
    if target_area == "Ginecologia e Obstetrícia":
        # Morte materna
        if any(re.search(p, text) for p in [r"morte materna", r"óbito materno", r"razão de mortalidade materna"]):
            return ("Ginecologia e Obstetrícia", "Morte materna")
        # Patologias vulvares / Disfunções
        if any(re.search(p, text) for p in [r"líquen escleroso", r"neoplasia intraepitelial vulvar", r"\bniv\b", r"glândula de bartholin", r"bartholin", r"cisto de bartholin"]):
            return ("Ginecologia e Obstetrícia", "Patologias da Vulva e Vagina")
        if any(re.search(p, text) for p in [r"disfunção sexual", r"vaginismo", r"dispareunia", r"anorgasmia", r"desejo sexual hipoativo"]):
            return ("Ginecologia e Obstetrícia", "Disfunções sexuais")
        if any(re.search(p, text) for p in [r"anatomia pélvica", r"ligamento largo", r"ligamento redondo", r"artéria uterina", r"assoalho pélvico"]):
            return ("Ginecologia e Obstetrícia", "Anatomia Pélvica")
        if any(re.search(p, text) for p in [r"fístula vesicovaginal", r"fístula retovaginal", r"fístula obstétrica"]):
            return ("Ginecologia e Obstetrícia", "Fístulas")
        # Cardiotocografia / Vitalidade
        if any(re.search(p, text) for p in [r"cardiotocografia", r"\bbcf\b", r"dip i\b", r"dip ii\b", r"dip iii\b", r"desaceleraç", r"perfil biofísico fetal", r"sofrimento fetal", r"dopplerfluxometria", r"artéria umbilical", r"ducto venoso"]):
            return ("Ginecologia e Obstetrícia", "Sofrimento Fetal")
        # Parto e Mecanismo
        if any(re.search(p, text) for p in [r"mecanismo de parto", r"estática fetal", r"plano de de lee", r"apresentação cefálica", r"variedade de posição", r"insinuação", r"assinclitismo", r"pelve feminina"]):
            return ("Ginecologia e Obstetrícia", "Estática fetal, Pelve e Mecanismo de Parto")
        if any(re.search(p, text) for p in [r"partograma", r"fase ativa", r"período expulsivo", r"secundamento", r"episiotomia", r"fórceps", r"vácuo-extrator", r"indução do parto", r"índice de bishop", r"misoprostol", r"ocitocina"]):
            return ("Ginecologia e Obstetrícia", "Assistência ao Parto")
        if any(re.search(p, text) for p in [r"trabalho de parto prematuro", r"\btpp\b", r"tocolítico", r"tocólise", r"corticoide antenatal", r"sulfato de magnésio neuroproteção"]):
            return ("Ginecologia e Obstetrícia", "Trabalho de parto prematuro")
        if any(re.search(p, text) for p in [r"rotura prematura de membranas", r"\brpmo\b", r"amniorrexe", r"corioamnionite", r"cristalização"]):
            return ("Ginecologia e Obstetrícia", "Rotura Prematura de Membranas Ovulares e Infecção Ovular")
        if any(re.search(p, text) for p in [r"puerpério", r"hemorragia pós-parto", r"atonia uterina", r"loquiação", r"infecção puerperal", r"endometrite puerperal"]):
            return ("Ginecologia e Obstetrícia", "Puerpério")
        # Sangramentos
        if any(re.search(p, text) for p in [r"abortamento", r"ameaça de aborto", r"aborto retido", r"gravidez ectópica", r"prenhez ectópica", r"mola hidatiforme", r"doença trofoblástica"]):
            return ("Ginecologia e Obstetrícia", "Sangramento da Primeira Metade da Gestação")
        if any(re.search(p, text) for p in [r"placenta prévia", r"descolamento prematuro de placenta", r"\bdpp\b", r"rotura de vasa prévia", r"rotura uterina"]):
            return ("Ginecologia e Obstetrícia", "Sangramento da Segunda Metade da Gestação")
        # Patologias na gestação
        if any(re.search(p, text) for p in [r"pré-eclâmpsia", r"eclâmpsia", r"síndrome hellp", r"hipertensão gestacional", r"sulfato de magnésio", r"hidralazina"]):
            return ("Ginecologia e Obstetrícia", "Síndromes Hipertensivas da Gestação")
        if any(re.search(p, text) for p in [r"diabetes gestacional", r"\bdmg\b", r"totg", r"glicemia de jejum na gestante"]):
            return ("Ginecologia e Obstetrícia", "Diabetes mellitus na gravidez")
        if any(re.search(p, text) for p in [r"hiv na gestação", r"sífilis na gestação", r"toxoplasmose na gestação", r"zika na gestação", r"estreptococo do grupo b", r"\begb\b", r"swab retovaginal"]):
            return ("Ginecologia e Obstetrícia", "Hepatites virais, HIV/AIDS e outras infecções na gestação")
        if any(re.search(p, text) for p in [r"restrição de crescimento intrauterino", r"\brciu\b", r"isoimunização rh", r"coombs indireto", r"gemelaridade", r"transfusão feto-fetal"]):
            return ("Ginecologia e Obstetrícia", "Medicina Fetal")
        if any(re.search(p, text) for p in [r"pré-natal", r"suplementação de ácido fólico", r"consultas de pré-natal", r"vacinação na gestante"]):
            return ("Ginecologia e Obstetrícia", "Pré-Natal")
        # Ginecologia Geral
        if any(re.search(p, text) for p in [r"contracepção", r"anticoncepcional", r"anticoncepção", r"\bdiu\b", r"levonorgestrel", r"laqueadura", r"método contraceptivo"]):
            return ("Ginecologia e Obstetrícia", "Contracepção")
        if any(re.search(p, text) for p in [r"climatério", r"menopausa", r"fogachos", r"terapia de reposição hormonal", r"\btrh\b", r"osteoporose pós-menopausa"]):
            return ("Ginecologia e Obstetrícia", "Climatério")
        if any(re.search(p, text) for p in [r"síndrome dos ovários policísticos", r"\bsop\b", r"amenorreia", r"hirsutismo", r"critérios de rotterdam"]):
            return ("Ginecologia e Obstetrícia", "Amenorreias e Síndrome dos Ovários Policísticos")
        if any(re.search(p, text) for p in [r"ciclo menstrual", r"eixo hipotálamo-hipófise-ovário", r"fase folicular", r"fase lútea", r"ovulação", r"\blh\b", r"\bfsh\b"]):
            return ("Ginecologia e Obstetrícia", "Ciclo Menstrual")
        if any(re.search(p, text) for p in [r"câncer de mama", r"carcinoma ductal", r"\bbirads\b", r"mamografia", r"quadrantectomia", r"linfonodo sentinela"]):
            return ("Ginecologia e Obstetrícia", "Tumores Malignos da Mama")
        if any(re.search(p, text) for p in [r"fibroadenoma", r"cisto mamário", r"mastite", r"descarga papilar", r"alteração funcional benigna da mama"]):
            return ("Ginecologia e Obstetrícia", "Doenças Benignas da Mama")
        if any(re.search(p, text) for p in [r"câncer de ovário", r"tumor ovariano", r"teratoma", r"cistoadenoma", r"torção anexial", r"ca-125"]):
            return ("Ginecologia e Obstetrícia", "Tumores dos Ovários")
        if any(re.search(p, text) for p in [r"câncer de endométrio", r"hiperplasia endometrial", r"espessamento endometrial", r"sangramento pós-menopausa"]):
            return ("Ginecologia e Obstetrícia", "Doenças do Corpo Uterino e Endométrio")
        if any(re.search(p, text) for p in [r"mioma", r"leiomioma", r"miomatose", r"sangramento uterino anormal", r"\bsua\b", r"palm-coein"]):
            return ("Ginecologia e Obstetrícia", "PALM-COEIN")
        if any(re.search(p, text) for p in [r"endometriose", r"adenomiose", r"dismenorreia", r"dispareunia", r"dor pélvica crônica"]):
            return ("Ginecologia e Obstetrícia", "Dor pélvica crônica")
        if any(re.search(p, text) for p in [r"doença inflamatória pélvica", r"\bdip\b", r"salpingite", r"violência sexual", r"profilaxia pós-violência"]):
            return ("Ginecologia e Obstetrícia", "Doença Inflamatória Pélvica e Violência Sexual")
        if any(re.search(p, text) for p in [r"candidíase", r"vaginose bacteriana", r"tricomoníase", r"leucorreia", r"prurido vulvar", r"clue cells"]):
            return ("Ginecologia e Obstetrícia", "Vulvovaginites")
        if any(re.search(p, text) for p in [r"cancro", r"úlcera genital", r"herpes genital", r"linfogranuloma venéreo", r"donovanose"]):
            return ("Ginecologia e Obstetrícia", "Úlceras genitais")
        if any(re.search(p, text) for p in [r"incontinência urinária", r"estudo urodinâmico", r"prolapso genital", r"cistocele", r"retocele"]):
            return ("Ginecologia e Obstetrícia", "Incontinência Urinária e Prolapsos de Órgãos Pélvicos")
        if any(re.search(p, text) for p in [r"infertilidade", r"espermograma", r"histerossalpingografia", r"reprodução assistida"]):
            return ("Ginecologia e Obstetrícia", "Infertilidade conjugal")
        if any(re.search(p, text) for p in [r"câncer de colo uterino", r"carcinoma espinocelular de colo", r"estadiamento figo colo"]):
            return ("Ginecologia e Obstetrícia", "Tumores do colo uterino")
        if any(re.search(p, text) for p in [r"papanicolau", r"citopatológico", r"preventivo", r"\bhpv\b", r"colposcopia", r"nic i", r"nic ii", r"nic iii", r"asc-us", r"asc-h", r"hsil", r"lsil", r"conização"]):
            return ("Ginecologia e Obstetrícia", "Rastreamento do Câncer de Colo Uterino")
        return ("Ginecologia e Obstetrícia", "Rastreamento do Câncer de Colo Uterino")

    # =====================================================================
    # 4. CIRURGIA
    # =====================================================================
    if target_area == "Cirurgia":
        # Disfagia e Dispepsia
        if any(re.search(p, text) for p in [r"disfagia", r"megaesôfago", r"acalásia", r"esôfago de barrett", r"divertículo de zenker"]):
            return ("Cirurgia", "Síndrome Disfágica")
        if any(re.search(p, text) for p in [r"dispepsia", r"úlcera péptica", r"h\. pylori", r"gastrite"]):
            return ("Cirurgia", "Síndrome Dispéptica")
        # Hemorragia Digestiva
        if any(re.search(p, text) for p in [r"hemorragia digestiva", r"hematêmese", r"melena", r"hematoquezia", r"varizes esofágicas", r"úlcera péptica sangrante", r"forrest", r"mallory-weiss"]):
            return ("Cirurgia", "Hemorragia Digestiva")
        # Abdome agudo
        if any(re.search(p, text) for p in [r"apendicite", r"diverticulite", r"abdome agudo inflamatório"]):
            return ("Cirurgia", "Abdome Agudo Inflamatório")
        if any(re.search(p, text) for p in [r"obstrução intestinal", r"volvo", r"bridas", r"aderências", r"íleo biliar", r"abdome agudo obstrutivo"]):
            return ("Cirurgia", "Abdome Agudo Obstrutivo")
        if any(re.search(p, text) for p in [r"úlcera perfurada", r"pneumoperitônio", r"abdome agudo perfurativo"]):
            return ("Cirurgia", "Abdome Agudo Perfurativo")
        if any(re.search(p, text) for p in [r"isquemia mesentérica", r"embolia mesentérica", r"abdome agudo isquêmico"]):
            return ("Cirurgia", "Abdome Agudo Isquêmico")
        # Vias biliares e pâncreas
        if any(re.search(p, text) for p in [r"colelitíase", r"colecistite", r"coledocolitíase", r"colangite", r"tríade de charcot", r"pêntade de reynolds", r"vias biliares"]):
            return ("Cirurgia", "Afecções Benignas das Vias Biliares")
        if any(re.search(p, text) for p in [r"pancreatite aguda", r"pancreatite crônica", r"cisto pancreático", r"necrose pancreática"]):
            return ("Cirurgia", "Afecções Pancreáticas")
        # Hérnias e Cirurgia da Parede
        if any(re.search(p, text) for p in [r"hérnia inguinal", r"hérnia femoral", r"hérnia incisional", r"hérnia umbilical", r"lichtenstein", r"shouldice"]):
            return ("Cirurgia", "Hérnias")
        # Trauma
        if any(re.search(p, text) for p in [r"trauma raquimedular", r"\btrm\b", r"choque neurogênico", r"choque medular", r"fratura de coluna", r"coluna cervical"]):
            return ("Cirurgia", "Trauma da Coluna Vertebral (TRM)")
        if any(re.search(p, text) for p in [r"atls", r"xabcde", r"via aérea definitiva", r"intubação em sequência rápida", r"colar cervical"]):
            return ("Cirurgia", "Abordagem Inicial (xABCDE)")
        if any(re.search(p, text) for p in [r"trauma abdominal", r"fast", r"laparotomia exploradora no trauma", r"lesão esplênica", r"lesão hepática no trauma"]):
            return ("Cirurgia", "Trauma Abdominal")
        if any(re.search(p, text) for p in [r"trauma torácico", r"pneumotórax hipertensivo", r"hemotórax maciço", r"tamponamento cardíaco", r"drenagem de tórax"]):
            return ("Cirurgia", "Trauma Torácico")
        if any(re.search(p, text) for p in [r"traumatismo cranioencefálico", r"\btce\b", r"escala de coma de glasgow", r"hematoma epidural", r"hematoma subdural", r"pic"]):
            return ("Cirurgia", "Trauma Cranioencefálico (TCE)")
        if any(re.search(p, text) for p in [r"trauma de face", r"le fort", r"trauma cervical", r"zona i cervical", r"zona ii cervical"]):
            return ("Cirurgia", "Trauma de Face e Pescoço")
        if any(re.search(p, text) for p in [r"fratura exposta", r"síndrome compartimental", r"trauma de extremidade", r"esmagamento"]):
            return ("Cirurgia", "Trauma de membros e extremidades")
        # Queimaduras
        if any(re.search(p, text) for p in [r"queimadura", r"parkland", r"regra dos nove", r"queimadura elétrica", r"inalação de fumaça"]):
            return ("Cirurgia", "Queimaduras")
        # Ortopedia
        if any(re.search(p, text) for p in [r"tendinite", r"bursite", r"fasceíte plantar", r"epicondilite", r"tenossinovite"]):
            return ("Cirurgia", "Tendinites/ Tenossinovites/ Fasceítes e Bursites")
        if any(re.search(p, text) for p in [r"luxação", r"entorse", r"ligamento cruzado", r"menisco", r"lesão ligamentar", r"manguito rotador"]):
            return ("Cirurgia", "Luxações/ Lesões Ligamentares")
        if any(re.search(p, text) for p in [r"ortopedia infantil", r"displasia do desenvolvimento do quadril", r"pé torto", r"epifisiólise"]):
            return ("Cirurgia", "Ortopedia Pediátrica")
        if any(re.search(p, text) for p in [r"osteossarcoma", r"tumor ósseo", r"sarcoma de ewing", r"sarcoma ósseo"]):
            return ("Cirurgia", "Tumores Ortopédicos")
        if any(re.search(p, text) for p in [r"fratura", r"consolidação óssea", r"osteossíntese", r"rádio distal", r"colo do fêmur", r"tíbia"]):
            return ("Cirurgia", "Fraturas Ósseas")
        # Vascular e Cardíaca
        if any(re.search(p, text) for p in [r"aneurisma de aorta", r"\baaa\b", r"dissecção de aorta"]):
            return ("Cirurgia", "Aneurismas")
        if any(re.search(p, text) for p in [r"doença arterial obstrutiva", r"claudicação", r"oclusão arterial aguda", r"isquemia crítica"]):
            return ("Cirurgia", "Doença arterial periférica")
        if any(re.search(p, text) for p in [r"varizes de membros", r"trombose venosa profunda", r"insuficiência venosa crônica"]):
            return ("Cirurgia", "Doenças Venosas")
        if any(re.search(p, text) for p in [r"cirurgia cardíaca", r"revascularização miocárdica", r"troca valvar cirúrgica", r"circulação extracorpórea"]):
            return ("Cirurgia", "Cirurgia Cardíaca")
        # Oncologia Cirúrgica e Digestivo
        if any(re.search(p, text) for p in [r"câncer gástrico", r"câncer de esôfago", r"câncer de pâncreas", r"câncer colorretal", r"adenocarcinoma de cólon"]):
            return ("Cirurgia", "Tumores do Aparelho Digestivo")
        if any(re.search(p, text) for p in [r"câncer de pulmão", r"timoma", r"nódulo pulmonar solitário", r"mediastino"]):
            return ("Cirurgia", "Tumores Pulmonares e Do Mediastino")
        if any(re.search(p, text) for p in [r"câncer de próstata", r"câncer renal", r"câncer de bexiga", r"tumor testicular"]):
            return ("Cirurgia", "Tumores Urológicos")
        if any(re.search(p, text) for p in [r"melanoma", r"carcinoma basocelular", r"\bcbc\b", r"carcinoma espinocelular cutâneo", r"\bcec\b"]):
            return ("Cirurgia", "Tumores Dermatológicos")
        if any(re.search(p, text) for p in [r"câncer de tireoide", r"tumor de parótida", r"esvaziamento cervical", r"tireoidectomia"]):
            return ("Cirurgia", "Tumores de Cabeça e Pescoço")
        if any(re.search(p, text) for p in [r"sarcoma de partes moles", r"lipossarcoma"]):
            return ("Cirurgia", "Tumores de partes moles")
        if any(re.search(p, text) for p in [r"polipose", r"síndrome de lynch", r"polipose adenomatosa familiar", r"\bpaf\b"]):
            return ("Cirurgia", "Polipose intestinal")
        if any(re.search(p, text) for p in [r"doença de crohn", r"retocolite ulcerativa"]):
            return ("Cirurgia", "Doença Inflamatória Intestinal")
        # Cuidados Pré/Pós e Técnica
        if any(re.search(p, text) for p in [r"risco cirúrgico", r"avaliação pré-operatória", r"jejum pré-operatório", r"asa \b"]):
            return ("Cirurgia", "Cuidados Pré-operatórios")
        if any(re.search(p, text) for p in [r"complicação pós-operatória", r"febre no pós-operatório", r"deiscência", r"infecção de sítio cirúrgico", r"atelectasia pós"]):
            return ("Cirurgia", "Cuidados e Complicações Pós-Operatórias")
        if any(re.search(p, text) for p in [r"fios de sutura", r"técnica cirúrgica", r"incisões cirúrgicas", r"drenos cirúrgicos"]):
            return ("Cirurgia", "Técnica Operatória")
        if any(re.search(p, text) for p in [r"enxerto de pele", r"retalho cutâneo", r"cicatrização", r"ferida"]):
            return ("Cirurgia", "Feridas, Enxertos e Retalhos")
        if any(re.search(p, text) for p in [r"anestesia geral", r"raquianestesia", r"bloqueio peridural", r"hipertermia maligna"]):
            return ("Cirurgia", "Anestesia")
        if any(re.search(p, text) for p in [r"cirurgia bariátrica", r"bypass gástrico", r"sleeve", r"obesidade mórbida"]):
            return ("Cirurgia", "Cirurgia da Obesidade")
        if any(re.search(p, text) for p in [r"hiperplasia prostática benigna", r"\bhpb\b", r"litíase urinária", r"cálculo renal", r"cólica nefrética"]):
            return ("Cirurgia", "Afecções Urológicas Benignas")
        if any(re.search(p, text) for p in [r"cirurgia pediátrica", r"estenose hipertrófica do piloro", r"atresia de esôfago", r"hérnia diafragmática congênita"]):
            return ("Cirurgia", "Cirurgia Pediátrica")
        if any(re.search(p, text) for p in [r"oftalmologia", r"glaucoma", r"catarata", r"descolamento de retina"]):
            return ("Cirurgia", "Oftalmologia")
        return ("Cirurgia", "Cuidados e Complicações Pós-Operatórias")

    # =====================================================================
    # 5. CLÍNICA MÉDICA
    # =====================================================================
    if target_area == "Clínica Médica":
        # Vasculites
        if any(re.search(p, text) for p in [r"vasculite anca", r"granulomatose de wegener", r"panarterite nodosa", r"churg-strauss", r"takayasu", r"vasculite"]):
            return ("Clínica Médica", "Vasculites")
        # Intoxicações
        if any(re.search(p, text) for p in [r"intoxicação", r"botrópico", r"crotálico", r"lachesis", r"escorpião", r"escorpionismo", r"paracetamol", r"organofosforado", r"antídoto"]):
            return ("Clínica Médica", "Intoxicações Exógenas e Acidentes por Animais Peçonhentos")
        # Doenças intersticiais
        if any(re.search(p, text) for p in [r"fibrose pulmonar", r"pneumonite por hipersensibilidade", r"sarcoidose", r"doença pulmonar intersticial"]):
            return ("Clínica Médica", "Doenças pulmonares intersticiais")
        # Fraqueza muscular e neurologia
        if any(re.search(p, text) for p in [r"guillain-barré", r"miastenia gravis", r"esclerose múltipla", r"esclerose lateral amiotrófica", r"\bela\b", r"fraqueza muscular"]):
            return ("Clínica Médica", "Síndromes Neurológicas e Fraqueza Muscular")
        # Nefrologia
        if any(re.search(p, text) for p in [r"glomerulonefrite", r"síndrome nefrítica", r"síndrome nefrótica", r"lesão mínima", r"nefropatia por iga", r"doença de berger", r"glomerulosclerose", r"tubulopatia"]):
            return ("Clínica Médica", "Glomerulopatias e Tubulopatias")
        if any(re.search(p, text) for p in [r"injúria renal aguda", r"\bira\b", r"doença renal crônica", r"\bdrc\b", r"hemodiálise", r"uremia", r"kdigo"]):
            return ("Clínica Médica", "Insuficiência Renal")
        if any(re.search(p, text) for p in [r"hiponatremia", r"hipernatremia", r"hipocalemia", r"hipercalemia", r"acidose metabólica", r"alcalose metabólica", r"gasometria arterial"]):
            return ("Clínica Médica", "Distúrbios Hidroeletrolíticos e Acidobásicos")
        # Cardiologia
        if any(re.search(p, text) for p in [r"infarto agudo do miocárdio", r"\biam\b", r"angina instável", r"supra de st", r"síndrome coronariana aguda", r"troponina"]):
            return ("Clínica Médica", "Síndrome Coronariana e Diagnósticos Diferenciais")
        if any(re.search(p, text) for p in [r"insuficiência cardíaca", r"\bic\b", r"fração de ejeção", r"bnp", r"ieca", r"betabloqueador", r"espironolactona"]):
            return ("Clínica Médica", "Insuficiência Cardíaca")
        if any(re.search(p, text) for p in [r"hipertensão arterial", r"\bhas\b", r"crise hipertensiva", r"emergência hipertensiva", r"mapa", r"mrpa"]):
            return ("Clínica Médica", "Hipertensão Arterial Sistêmica")
        if any(re.search(p, text) for p in [r"fibrilação atrial", r"flutter", r"taquicardia ventricular", r"bloqueio atrioventricular", r"pcr no adulto", r"acls"]):
            return ("Clínica Médica", "Arritmias, Síncope e PCR")
        if any(re.search(p, text) for p in [r"valvopatia", r"estenose mitral", r"insuficiência mitral", r"estenose aórtica", r"insuficiência aórtica", r"miocardiopatia", r"cardiomiopatia"]):
            return ("Clínica Médica", "Valvopatias e Cardiomiopatias")
        if any(re.search(p, text) for p in [r"endocardite infecciosa", r"critérios de duke", r"bacteremia", r"infecção de corrente sanguínea"]):
            return ("Clínica Médica", "Endocardite e Infecção de Corrente Sanguínea")
        # Pneumologia
        if any(re.search(p, text) for p in [r"pneumonia adquirida na comunidade", r"\bpac\b", r"curb-65", r"influenza", r"síndrome respiratória aguda grave"]):
            return ("Clínica Médica", "Pneumonias e Síndromes Gripais")
        if any(re.search(p, text) for p in [r"tuberculose", r"baciloscopia", r"\bbaar\b", r"esquema ripe", r"rifampicina", r"isoniazida"]):
            return ("Clínica Médica", "Tuberculose")
        if any(re.search(p, text) for p in [r"asma no adulto", r"dpoc", r"espirometria", r"broncodilatador", r"corticoide inalatório", r"gold \b"]):
            return ("Clínica Médica", "Distúrbios Obstrutivos")
        if any(re.search(p, text) for p in [r"tromboembolismo pulmonar", r"\btep\b", r"escore de wells", r"angiotomografia de tórax", r"hipertensão pulmonar"]):
            return ("Clínica Médica", "Embolia Pulmonar e Hipertensão Pulmonar")
        if any(re.search(p, text) for p in [r"sara", r"ventilação mecânica", r"peep", r"pneumointensivismo"]):
            return ("Clínica Médica", "Pneumointensivismo")
        # Endocrinologia e Metabologia
        if any(re.search(p, text) for p in [r"diabetes mellitus", r"cetoacidose diabética", r"estado hiperosmolar", r"insulina", r"metformina", r"hemoglobina glicada"]):
            return ("Clínica Médica", "Diabetes")
        if any(re.search(p, text) for p in [r"hipotireoidismo", r"hipertireoidismo", r"doença de graves", r"tireoidite de hashimoto", r"tsh", r"t4 livre"]):
            return ("Clínica Médica", "Tireoide")
        if any(re.search(p, text) for p in [r"síndrome metabólica", r"dislipidemia", r"estatina", r"colesterol", r"triglicerídeos"]):
            return ("Clínica Médica", "Síndrome Metabólica e Dislipidemia")
        if any(re.search(p, text) for p in [r"síndrome de cushing", r"insuficiência adrenal", r"doença de addison", r"feocromocitoma", r"hiperparatireoidismo"]):
            return ("Clínica Médica", "Paratireoides, Suprarrenal e Outras Síndromes Endócrinas")
        # Gastroenterologia e Hepatologia
        if any(re.search(p, text) for p in [r"cirrose hepática", r"hipertensão portal", r"ascite", r"peritonite bacteriana espontânea", r"\bpbe\b", r"encefalopatia hepática"]):
            return ("Clínica Médica", "Cirrose, Insuficiência Hepática e Complicações")
        if any(re.search(p, text) for p in [r"hepatite a", r"hepatite b", r"hepatite c", r"sorologia hepatite", r"doença de gilbert", r"crigler-najjar"]):
            return ("Clínica Médica", "Hepatites e Doenças do Metabolismo da Bilirrubina")
        # Infectologia
        if any(re.search(p, text) for p in [r"hiv no adulto", r"aids", r"tarv", r"contagem de cd4", r"carga viral", r"infecção oportunista"]):
            return ("Clínica Médica", "HIV e AIDS no Adulto Não Gestante")
        if any(re.search(p, text) for p in [r"meningite bacteriana", r"meningite viral", r"líquor", r"punção lombar", r"encefalite"]):
            return ("Clínica Médica", "Infecções do Sistema Nervoso Central")
        if any(re.search(p, text) for p in [r"dengue", r"chikungunya", r"febre amarela", r"malária", r"leptospirose", r"leishmaniose", r"síndrome febril"]):
            return ("Clínica Médica", "Síndromes Febris")
        if any(re.search(p, text) for p in [r"sífilis adquirida", r"gonorreia", r"clamídia", r"cancro mole", r"doença sexualmente transmissível"]):
            return ("Clínica Médica", "Doenças Sexualmente Transmissíveis")
        if any(re.search(p, text) for p in [r"erisipela", r"celulite infecciosa", r"osteomielite no adulto", r"artrite séptica no adulto"]):
            return ("Clínica Médica", "Infecções de Pele, Ossos e Partes Moles")
        if any(re.search(p, text) for p in [r"hanseníase", r"leishmaniose tegumentar", r"esporotricose", r"paracoccidioidomicose"]):
            return ("Clínica Médica", "Doenças Infectoparasitárias com Acometimento Dermatológico")
        # Hematologia
        if any(re.search(p, text) for p in [r"anemia ferropriva no adulto", r"anemia megaloblástica", r"anemia falciforme", r"talassemia", r"anemia hemolítica"]):
            return ("Clínica Médica", "Anemias e Hemoglobinopatias")
        if any(re.search(p, text) for p in [r"púrpura trombocitopênica", r"\bpti\b", r"\bptt\b", r"hemofilia", r"coagulação intravascular disseminada", r"\bcivd\b", r"transfusão de hemocomponentes"]):
            return ("Clínica Médica", "Distúrbios da Hemostasia, Desordens Trombóticas e Transfusão de Hemocomponentes")
        if any(re.search(p, text) for p in [r"leucemia", r"linfoma de hodgkin", r"linfoma não-hodgkin", r"mieloma múltiplo"]):
            return ("Clínica Médica", "Onco-Hematologia")
        # Neurologia
        if any(re.search(p, text) for p in [r"acidente vascular cerebral", r"\bavc\b", r"trombólise no avc", r"escala nihss", r"avc isquêmico", r"avc hemorrágico"]):
            return ("Clínica Médica", "AVC")
        if any(re.search(p, text) for p in [r"cefaleia tensional", r"enxaqueca", r"migrânea", r"cefaleia em salvas", r"arterite de células gigantes"]):
            return ("Clínica Médica", "Cefaleias")
        if any(re.search(p, text) for p in [r"doença de alzheimer", r"demência vascular", r"demência por corpos de lewy", r"avaliação geriátrica", r"quedas no idoso"]):
            return ("Clínica Médica", "Geriatria e Demências")
        if any(re.search(p, text) for p in [r"morte encefálica", r"doação de órgãos", r"neurointensivismo"]):
            return ("Clínica Médica", "Neurointensivismo e Ética Médica")
        # Reumatologia
        if any(re.search(p, text) for p in [r"artrite reumatoide", r"gota", r"artrite microcristalina", r"espondilite anquilosante"]):
            return ("Clínica Médica", "Artrites e Diagnósticos Diferenciais")
        if any(re.search(p, text) for p in [r"lúpus eritematoso sistêmico", r"\bles\b", r"esclerose sistêmica", r"polimiosite", r"dermatomiosite", r"síndrome de sjögren"]):
            return ("Clínica Médica", "Colagenoses e Miopatias")
        # Dermatologia
        if any(re.search(p, text) for p in [r"farmacodermia", r"síndrome de stevens-johnson", r"net", r"psoríase", r"dermatite atópica", r"eczema", r"dermatoses"]):
            return ("Clínica Médica", "Farmacodermias e Dermatoses")
        # Psiquiatria
        if any(re.search(p, text) for p in [r"transtorno depressivo", r"transtorno bipolar", r"esquizofrenia", r"transtorno de ansiedade", r"transtorno do pânico"]):
            return ("Clínica Médica", "Transtornos Mentais")
        if any(re.search(p, text) for p in [r"alcoolismo", r"abstinência alcoólica", r"delirium tremens", r"tabagismo", r"dependência química", r"cocaína"]):
            return ("Clínica Médica", "Abuso de Álcool, Tabaco e Outras Substâncias")
        if any(re.search(p, text) for p in [r"reforma psiquiátrica", r"caps na saúde mental", r"luta antimanicomial"]):
            return ("Clínica Médica", "Saúde Mental no Brasil")
        # Emergências / Choque
        if any(re.search(p, text) for p in [r"sepse no adulto", r"choque séptico", r"surviving sepsis", r"qsofa", r"drogas vasoativas"]):
            return ("Clínica Médica", "Sepse, Choque Séptico e Outros tipos de Choque")

        return ("Clínica Médica", "Síndromes Febris")

# Apply refined updates
updates = []
for q in questions:
    a, s = classify_question_refined(q)
    updates.append((a, s, q["id"]))

conn.executemany("UPDATE questions SET area = ?, subtema = ? WHERE id = ?", updates)
conn.commit()
print("Refined classification applied!")
