import json
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")

with open('canonical_taxonomy_170.json', encoding='utf-8') as f:
    TAX_170 = json.load(f)

ALL_CANONICAL = {}
for area, themes in TAX_170.items():
    for t in themes:
        ALL_CANONICAL[t] = area

def norm(text):
    text = unicodedata.normalize('NFD', str(text or ''))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().strip()

def classify_ped_item(q):
    stem = q.get('stem', '')
    alts = q.get('alternatives', '')
    exp = q.get('explanation', '')
    topic = q.get('topic', '')
    cur_sub = q.get('current_subtema', '')
    
    full_text = f"{topic} {stem} {alts} {exp}"
    fn = norm(full_text)
    sn = norm(stem)
    tn = norm(topic)
    
    # =========================================================================
    # 1. CIRURGIA / TRAUMA / CIRURGIA PEDIÁTRICA & ORTOPEDIA
    # =========================================================================
    # Wilms tumor
    if any(k in fn for k in ['tumor de wilms', 'nefroblastoma', 'massa palpavel no flanco', 'massa abdominal no flanco']) and not any(k in fn for k in ['neuroblastoma', 'nefritica']):
        if 'wilms' in fn or 'nefroblastoma' in fn:
            return "Cirurgia", "Uro-Oncologia: Câncer de Próstata, Rim, Bexiga e Testículo", "Neoplasia renal maligna na infância (Tumor de Wilms / Nefroblastoma)."

    # Pediatric Orthopedics
    if any(k in fn for k in ['displasia do desenvolvimento do quadril', 'displasia de quadril', 'ortolani', 'barlow', 'galeazzi', 'pe torto congenito', 'ponseti', 'epifisiolise', 'epifisiolistese', 'legg-calve-perthes', 'sinovite transitoria', 'claudicacao na infancia', 'dor no quadril', 'manobra de ortolani', 'manobra de barlow', 'sinal de galeazzi', 'subluxacao da cabeca do radio', 'cotovelo de babylong', 'pronacao dolorosa']):
        return "Cirurgia", "Ortopedia Pediátrica: Displasia do Quadril, Pé Torto e Epifisiólise", "Afecções ortopédicas pediátricas clássicas, quadril e membros infantis."

    # Pediatric Burn
    if any(k in fn for k in ['queimadura', 'queimado', 'superficie corporal queimada', 'scq']) and any(k in sn for k in ['lactente', 'meses', 'crianca', 'menino', 'menina', 'anos de idade', 'pre-escolar', 'escolar']):
        return "Cirurgia", "Particularidades das Queimaduras na Faixa Etária Pediátrica", "Atendimento, ressuscitação volêmica e particularidades do paciente queimado na faixa etária pediátrica."

    # Pediatric Surgery & Neonatal Digestive Malformations
    if any(k in fn for k in [
        'esofagocoloplastia', 'atresia de esofago', 'fistula traqueoesofagica', 'atresia duodenal', 'dupla bolha', 'atresia intestinal', 
        'onfalocele', 'gastrosquise', 'estenose hipertrofica do piloro', 'oliva pilorica', 'piloromiotomia', 'fredet-ramstedt',
        'intussuscepcao', 'invaginacao intestinal', 'sinal de dance', 'enema opaco', 'fezes em geleia', 'fezes em framboesa',
        'doenca de hirschsprung', 'megacolon aganglionar', 'abaixamento de colon', 'swenson', 'duhamel', 'soave',
        'anomalia anorretal', 'atresia anal', 'cloaca persistente', 'fistula retoperineal', 'fistula retovestibular', 'fistula retouretral',
        'cisto de coledoco', 'atresia de vias biliares', 'cirurgia de kasai', 'portoenterostomia',
        'diverticulo de meckel', 'cintilografia com tecnecio-99m', 'mucosa gastrica ectopica', 'malrotacao intestinal', 'volvo de intestino medio', 'sinal do redemoinho', 'ladoppen', 'cirurgia de ladd',
        'vacterl', 'hernia diafragmatica congenita', 'bochdalek', 'morgagni'
    ]):
        return "Cirurgia", "Cirurgia Pediátrica e Malformações Digestivas Neonatais", "Malformações congênitas digestivas, patologias cirúrgicas neonatais e pediátricas."

    # Inguinal / Abdominal Hernias
    if any(k in fn for k in ['hernia inguinal', 'hernia encarcerada', 'hernia estrangulada', 'hernia umbilical', 'hernia epigastrica']) and 'hernia' in sn:
        return "Cirurgia", "Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)", "Hérnias da parede abdominal na infância e condutas cirúrgicas."

    # General thoracic surgery / mediastinal cysts
    if any(k in fn for k in ['cisto broncogenico', 'malformacao adenomatoide cistica', 'sequestro pulmonar', 'cisto do mediastino']):
        return "Cirurgia", "Câncer de Pulmão, Nódulo Pulmonar Solitário e Tumores do Mediastino", "Lesões congênitas e expansivas císticas/neoplásicas do mediastino e tórax."

    # Postop / Trauma thoracic
    if any(k in fn for k in ['hemotorax coagulado', 'vats', 'videotoracoscopia', 'drenagem pleural fechada', 'pneumotorax']):
        return "Cirurgia", "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco", "Trauma torácico, hemotórax, pneumotórax e abordagem pleural."

    # =========================================================================
    # 2. TOXICOLOGIA & ANIMAIS PEÇONHENTOS / DERMATO / ENDOCRINO / NEFRO / HEMATO (CLÍNICA MÉDICA)
    # =========================================================================
    # Scorpion / Spider / Snake / Envenomation
    if any(k in fn for k in ['escorpiao', 'escorpionico', 'tityus', 'aranha marrom', 'loxosceles', 'phoneutria', 'jararaca', 'bothrops', 'crotalus', 'cascavel', 'micrurus', 'coral verdadeira', 'animais peconhentos', 'intoxicacao exogena', 'chumbinho', 'organofosforado', 'atropina', 'pralidoxima', 'intoxicacao por paracetamol', 'n-acetilcisteina']):
        return "Clínica Médica", "Toxicologia Clínica e Acidentes por Animais Peçonhentos", "Manejo clínico de acidentes por animais peçonhentos e toxicologia clínica."

    # Diabetes / DKA in children
    if any(k in fn for k in ['cetoacidose diabetica', 'diabetes mellitus tipo 1', 'dm1', 'mody', 'glicemia de jejum > 126', 'cetonuria', 'kussmaul', 'insulinoterapia']):
        return "Clínica Médica", "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento", "Debute de Diabetes Mellitus tipo 1, cetoacidose diabética e manejo glicêmico."

    # Glomerular diseases (GNPE, Nefrotica, SHU)
    if any(k in fn for k in ['sindrome hemolitico-uremica', 'sindrome hemolitico uremica', 'shu', 'esquizocitos', 'microangiopatia trombotica']):
        return "Clínica Médica", "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias", "Síndrome Hemolítico-Urêmica pós-diarreica e microangiopatia trombótica."
    if any(k in fn for k in ['glomerulonefrite pos-estreptococica', 'gnpe', 'sindrome nefritica', 'sindrome nefrotica', 'lesao minima', 'corticodependente', 'dismorfismo eritrocitario', 'hematuria glomerular', 'nefropatia por iga', 'berger']):
        return "Clínica Médica", "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias", "Síndromes glomerulares (nefrítica, nefrótica e glomerulopatias) na infância."

    # Pediatric Hematology-Oncology (LLA, Lymphoma, Tumor Lysis)
    if any(k in fn for k in ['leucemia linfoide aguda', 'lla', 'leucemia mieloide aguda', 'linfoma de hodgkin', 'linfoma nao-hodgkin', 'sindrome de lise tumoral', 'neutropenia febril', 'mielograma', 'blastos']):
        return "Clínica Médica", "Leucemias, Linfomas e Mieloma Múltiplo", "Neoplasias hematológicas na infância, leucemias agudas e emergências oncológicas."

    # Coagulopathies (PTI, Hemophilia, VWD)
    if any(k in fn for k in ['purpura trombocitopenica imune', 'purpura trombocitopenica imunologica', 'pti', 'hemofilia a', 'hemofilia b', 'fator viii', 'fator ix', 'doenca de von willebrand', 'deficiencia de fator vii', 'tp inr prolongado com ttpa normal']):
        return "Clínica Médica", "Coagulopatias, Trombofilias, Púrpuras e Hemoterapia", "Distúrbios hemorrágicos hereditários e adquiridos, hemofilias e púrpuras."

    # Anemia differential / Thalassemia
    if any(k in fn for k in ['traco talassemico', 'talassemia minor', 'beta-talassemia', 'eletroforese de hemoglobina', 'esferocitose hereditaria', 'curva de fragilidade osmotica', 'anemia hemolitica autoimune']):
        return "Clínica Médica", "Diagnóstico Diferencial das Anemias e Hemoglobinopatias", "Diagnóstico diferencial das anemias hereditárias, hemoglobinopatias e talassemias."

    # Meningitis in older child / adolescent
    if any(k in fn for k in ['meningite viral', 'meningite bacteriana', 'meningite meningococica', 'pleocitose', 'glicorraquia', 'neisseria meningitidis']) and any(k in sn for k in ['10 anos', '11 anos', '12 anos', '13 anos', '14 anos', '15 anos', '16 anos', 'adolescente']):
        return "Clínica Médica", "Meningites, Encefalites e Infecções do SNC", "Meningites e infecções do sistema nervoso central no adolescente."

    # Guillain-Barre
    if any(k in fn for k in ['sindrome de guillain-barre', 'dissociacao albuminocitologica', 'paralisia flacida ascendente', 'polirradiculoneuropatia']):
        return "Clínica Médica", "Neuropatias Periféricas, Miastenia Gravis e Doenças Neuromusculares", "Polineuropatias agudas periféricas (Síndrome de Guillain-Barré) na infância."

    # Juvenile Dermatomyositis / SLE
    if any(k in fn for k in ['dermatomiosite juvenil', 'heliotropo', 'papulas de gottron', 'fraqueza muscular proximal', 'lupus eritematoso sistemico juvenil']):
        return "Clínica Médica", "Lúpus Eritematoso Sistêmico (LES), Esclerose Sistêmica e Miopatias Inflamatórias", "Miopatias inflamatórias e colagenoses autoimunes sistêmicas na infância."

    # Arbovirus / Dengue
    if any(k in fn for k in ['dengue', 'chikungunya', 'zika', 'prova do laco', 'hemoconcentracao']):
        if not any(k in fn for k in ['zika congenita', 'microcefalia por zika']):
            return "Clínica Médica", "Síndromes Febris Agudas e Arboviroses (Dengue, Chikungunya, Febre Amarela)", "Síndromes febris agudas e manejo clínico das arboviroses na infância."

    # Skin infections (Impetigo, Onicomicose, Erisipela)
    if any(k in fn for k in ['onicomicose', 'terbinafina']):
        return "Clínica Médica", "Dermatoses Infecciosas, Hanseníase e Leishmanioses", "Infecções fúngicas cutâneas e ungueais na infância e adolescência."
    if any(k in fn for k in ['impetigo bolhoso', 'impetigo crostoso', 'sindrome da pele escaldada', 'estafilococia cutanea']):
        return "Clínica Médica", "Celulite, Erisipela, Osteomielite e Infecções de Partes Moles", "Infecções bacterianas cutâneas e de partes moles na pediatria."

    # Electrolytes / Acid-Base
    if any(k in fn for k in ['hipercalemia', 'hipocalemia', 'gluconato de calcio', 'disturbio acidobasico', 'anion gap aumentado', 'acidose metabolica com anion gap', 'hiponatremia hipovolemica']):
        return "Clínica Médica", "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base", "Distúrbios hidroeletrolíticos e ácido-base na pediatria."

    # HIV vertical/pediatric
    if any(k in fn for k in ['crianca exposta ao hiv', 'diagnostico de hiv', 'carga viral do hiv', 'teste sorologico de hiv']):
        return "Clínica Médica", "Infecção pelo HIV: Diagnóstico, TARV e Infecções Oportunistas", "Diagnóstico, acompanhamento e profilaxia da infecção pelo HIV pediátrico."

    # =========================================================================
    # 3. PEDIATRIA CANÔNICA (28 TEMAS)
    # =========================================================================

    # Neonatology - Resuscitation & Delivery Room
    if any(k in fn for k in ['reanimacao neonatal', 'passos iniciais da reanimacao', 'ventilacao com pressao positiva', 'vpp em sala de parto', 'aspiracao de meconio', 'clampeamento oportuno', 'sala de parto', 'apgar', 'frequencia cardiaca < 100 ao nascer', 'massagem cardiaca neonatal']):
        return "Pediatria", "Reanimação Neonatal e Assistência em Sala de Parto", "Passos sistematizados de reanimação neonatal e assistência em sala de parto."

    # Neonatology - Rooming-in & Screening Tests
    if any(k in fn for k in ['alojamento conjunto', 'teste do pezinho', 'teste do olhinho', 'reflexo vermelho', 'teste do coracaozinho', 'oximetria de triagem', 'teste da orelhinha', 'emissao otoacustica', 'triagem neonatal', 'vitamina k neonatal', 'profilaxia da oftalmia', 'crede']):
        return "Pediatria", "Alojamento Conjunto e Testes de Triagem Neonatal (Pezinho, Olhinho, Coraçãozinho)", "Rotinas de alojamento conjunto, cuidados neonatais imediatos e testes de triagem."

    # Neonatology - Congenital Infections & Sepsis
    if any(k in fn for k in ['sifilis congenita', 'vdrl neonatal', 'toxoplasmose congenita', 'citomegalovirus congenito', 'cmv congenito', 'rubeola congenita', 'herpes neonatal', 'sepse neonatal precoce', 'sepse neonatal tardia', 'estreptococo do grupo b', 'streptococcus agalactiae', 'swab retovaginal']):
        return "Pediatria", "Neonatologia: Infecções Congênitas (TORCH) e Sepse Neonatal", "Infecções congênitas do grupo TORCH e sepse neonatal precoce/tardia."

    # Neonatology - Jaundice & Hematology
    if any(k in fn for k in ['ictericia neonatal', 'ictericia fisiologica', 'ictericia do leite materno', 'incompatibilidade abo', 'incompatibilidade rh', 'coombs direto positivo', 'fototerapia', 'exsanguineotransfusao', 'bilirrubina indireta neonatal', 'policitemia neonatal', 'anemia falciforme', 'crise aplasica', 'sequestro esplenico', 'sindrome toracica aguda', 'dactilite']):
        return "Pediatria", "Neonatologia: Icterícia Neonatal e Doenças Hematológicas", "Icterícia neonatal, isoimunização materno-fetal e hemoglobinopatias na infância."

    # Neonatology - Respiratory Distress & Hyaline Membrane
    if any(k in fn for k in ['doenca da membrana hialina', 'sindrome do desconforto respiratorio do rn', 'surfactante pulmonar', 'taquipneia transitoria do recem-nascido', 'ttrn', 'sindrome de aspiracao meconial', 'sam', 'displasia broncopulmonar', 'pneumotorax neonatal', 'desconforto respiratorio neonatal', 'silverman-andersen']):
        return "Pediatria", "Neonatologia: Desconforto Respiratório e Doença da Membrana Hialina", "Síndromes de desconforto respiratório do período neonatal e terapia com surfactante."

    # Neonatology - Metabolic & Hypoglycemia
    if any(k in fn for k in ['hipoglicemia neonatal', 'filho de mae diabetica', 'glicemia capilar < 40 no rn', 'hipocalcemia neonatal', 'hipomagnesemia neonatal']):
        return "Pediatria", "Neonatologia: Distúrbios Metabólicos e Hipoglicemia no Recém-Nascido", "Distúrbios metabólicos, hipoglicemia e desordens hidroeletrolíticas no período neonatal."

    # Neonatology - Asphyxia & Neurology
    if any(k in fn for k in ['asfixia perinatal', 'encefalopatia hipoxico-isquemica', 'hipotermia terapeutica', 'hemorragia peri-intraventricular', 'convulsao neonatal', 'sarnat']):
        return "Pediatria", "Neonatologia: Asfixia Perinatal, Encefalopatia e Doenças Neurológicas", "Asfixia perinatal, encefalopatia neonatal e lesões neurológicas do recém-nascido."

    # Vaccination & PNI
    if any(k in fn for k in ['vacina', 'vacinacao', 'calendario vacinal', 'pni', 'imunobiologico', 'bcg', 'pentavalente', 'poliomielite', 'vip', 'vop', 'triplice viral', 'tetraviral', 'febre amarela', 'soro antirrabico', 'profilaxia da raiva', 'varicela vacina', 'hpv vacina', 'meningococica']):
        return "Pediatria", "Calendário Vacinal do PNI e Imunizações Especiais", "Calendário Nacional de Imunização do PNI, esquemas especiais e profilaxias vacinais."

    # Exanthematic diseases
    if any(k in fn for k in ['sarampo', 'manchas de koplik', 'rubeola', 'exantema subito', 'roseola infantum', 'eritema infeccioso', 'parvovirus b19', 'bochechas esbofeteadas', 'varicela', 'catapora', 'mao-pe-boca', 'coxsackie', 'escarlatina', 'pastia', 'filatov', 'doencas exantematicas', 'diagnostico diferencial dos exantemas']):
        return "Pediatria", "Doenças Exantemáticas e Diagnóstico Diferencial dos Exantemas", "Diagnóstico diferencial, epidemiologia e conduta nas doenças exantemáticas na infância."

    # Parasites
    if any(k in fn for k in ['giardiase', 'giardia', 'ascaridiase', 'ascaris', 'enterobiase', 'enterobius', 'oxiuro', 'fita gomada', 'sindrome de loffler', 'ancilostomiase', 'necator', 'estrongiloidiase', 'strongyloides', 'amebiase', 'entamoeba', 'parasitose intestinal', 'helmintiase', 'protozoose', 'albendazol', 'nitazoxanida']):
        return "Pediatria", "Parasitoses Intestinais: Helmintíases e Protozooses", "Helmintíases, protozooses e parasitoses intestinais na infância."

    # Growth & DNPM / Puericultura
    if any(k in fn for k in ['marcos do desenvolvimento', 'dnpm', 'desenvolvimento neuropsicomotor', 'escala de denver', 'curva da oms', 'escore z', 'percentil de peso', 'estatura para idade', 'perimetro cefalico', 'puericultura', 'sustenta a cabeca', 'senta sem apoio', 'engatinha', 'anda com apoio', 'anda sozinho', 'pinca completa', 'sorriso social', 'balbucio', 'vocabulario de palavras']):
        return "Pediatria", "Puericultura: Marcos do Desenvolvimento (DNPM) e Curvas de Crescimento", "Acompanhamento de puericultura, marcos do desenvolvimento neuropsicomotor e curvas de crescimento da OMS."

    # Stature & Puberty
    if any(k in fn for k in ['baixa estatura', 'estatura baixa', 'idade ossea', 'velocidade de crescimento', 'puberdade precoce', 'puberdade tardia', 'atraso puberal', 'telarca precoce', 'adrenarca precoce', 'escala de tanner', 'estirao puberal', 'alvo genetico']):
        return "Pediatria", "Baixa Estatura, Puberdade Precoce e Atraso Puberal", "Investigação diagnóstica de baixa estatura, distúrbios puberais e estadiamento de Tanner."

    # Neurodevelopment & Mental Health
    if any(k in fn for k in ['transtorno do espectro autista', 'autismo', 'tea', 'transtorno de deficit de atencao', 'tdah', 'hiperatividade', 'transtornos do neurodesenvolvimento', 'saude mental na infancia', 'depressao na infancia', 'ansiedade na infancia']):
        return "Pediatria", "Transtornos do Neurodesenvolvimento (TEA, TDAH) e Saúde Mental na Infância", "Transtornos do neurodesenvolvimento, TEA, TDAH e saúde mental infantil."

    # Breastfeeding & Nutrition & Malnutrition
    if any(k in fn for k in ['aleitamento materno', 'leite materno', 'amamentacao', 'pega adequada', 'fissura mamilar', 'mastite lactacional', 'ingurgitamento mamario', 'alimentacao complementar', 'introducao alimentar', 'desnutricao infantil', 'kwashiorkor', 'marasmo', 'formula infantil', 'desmame']):
        return "Pediatria", "Aleitamento Materno, Alimentação Complementar e Desnutrição Infantil", "Promoção do aleitamento materno, técnicas de amamentação, introdução alimentar e desnutrição."

    # Nutritional deficiencies (Iron, Vit D)
    if any(k in fn for k in ['anemia ferropriva', 'suplementacao de ferro', 'ferro elementar profilatico', 'sulfato ferroso profilaxia', 'hipovitaminose d', 'vitamina d profilaxia', 'raquitismo carencial', 'carencia de micronutrientes']):
        return "Pediatria", "Anemias Carenciais e Distúrbios de Micronutrientes (Ferro, Vitamina D)", "Prevenção e tratamento da anemia ferropriva e distúrbios de micronutrientes (Ferro e Vitamina D)."

    # Diarrhea, Dehydration & Malabsorption
    if any(k in fn for k in ['diarreia aguda', 'gastroenterite aguda', 'desidratacao na crianca', 'terapia de reidratacao oral', 'tro', 'plano a', 'plano b', 'plano c', 'solucao de reidratacao oral', 'diarreia cronica', 'doenca celiaca', 'anticorpo antitransglutaminase', 'aplv', 'alergia a proteina do leite de vaca', 'linfangiectasia intestinal', 'enteropatia perdedora']):
        return "Pediatria", "Diarreia Aguda, Reidratação Oral e Doenças Disabsortivas", "Manejo da diarreia aguda, planos de reidratação (A, B, C) e doenças disabsortivas pediátricas."

    # Functional & Organic Constipation
    if any(k in fn for k in ['constipacao intestinal funcional', 'constipacao cronica', 'criterios de roma', 'encoprese', 'escape fecal', 'fecaloma', 'polietilenoglicol', 'peg 4000', 'laxativo osmico']):
        return "Pediatria", "Constipação Intestinal Funcional e Orgânica", "Diagnóstico, critérios de Roma e manejo da constipação intestinal funcional e orgânica."

    # Obstructive & Asthma & Bronchiolitis
    if any(k in fn for k in ['bronquiolite viral aguda', 'bva', 'virus sincicial respiratorio', 'vsr', 'asma na infancia', 'crise de asma na crianca', 'sibilancia', 'lactente sibilante', 'laringite aguda', 'crupe viral', 'laringotraqueobronquite', 'estridor laringeo', 'salbutamol', 'corticoide inalatorio', 'budesonida']):
        return "Pediatria", "Distúrbios Obstrutivos, Asma e Bronquiolite na Infância", "Doenças obstrutivas das vias aéreas inferiores, bronquiolite viral aguda e asma pediátrica."

    # Upper Airway Infections (OMA, Sinusite, Faringotonsilite)
    if any(k in fn for k in ['otite media aguda', 'oma', 'amoxicilina para oma', 'otite com efusao', 'rinossinusite aguda', 'sinusite bacteriana', 'faringoamigdalite', 'amigdalite estreptococica', 'streptococcus pyogenes', 'score de centor', 'resfriado comum', 'epiglotite aguda']):
        return "Pediatria", "Afecções de Vias Aéreas Superiores: OMA, Sinusite e Faringoamigdalite", "Infecções agudas de vias aéreas superiores (OMA, sinusite e faringoamigdalite bacteriana/viral)."

    # UTI & Vesicoureteral Reflux
    if any(k in fn for k in ['infeccao do trato urinario', 'itu na infancia', 'pielonefrite aguda na crianca', 'cistite na crianca', 'urocultura > 100.000', 'refluxo vesicoureteral', 'rvu', 'uretrocistografia miccional', 'ucm', 'dmsa', 'cintilografia renal', 'cicatriz renal']):
        return "Pediatria", "Infecção do Trato Urinário (ITU) e Refluxo Vesicoureteral na Infância", "Diagnóstico, investigação por imagem e manejo de ITU e refluxo vesicoureteral em pediatria."

    # Febrile seizures & Epilepsy
    if any(k in fn for k in ['convulsao febril', 'crise febril simples', 'crise febril complexa', 'epilepsia na infancia', 'sindrome de west', 'espasmos infantis', 'hipsarritmia', 'crise de ausencia', 'estado de mal epileptico']):
        return "Pediatria", "Convulsão Febril, Epilepsias e Síndromes Convulsivas na Infância", "Manejo da crise convulsiva febril, epilepsias infantis e estado de mal epiléptico."

    # Pediatric Sepsis, Shock & PALS
    if any(k in fn for k in ['sepse pediatrica', 'choque septico pediatrico', 'ressuscitacao hemodinamica pediatrica', 'choque compensado', 'choque descompensado', 'adrenalina no choque', 'dobutamina no choque', 'expansao volemica 20 ml/kg', 'pals', 'parada cardiorrespiratoria pediatrica', 'arritmia pediatrica', 'taquicardia supraventricular na crianca', 'adenosina']):
        if 'pals' in fn or 'arritmia' in fn or 'pcr' in fn or 'parada' in fn or 'taquicardia supraventricular' in fn:
            return "Pediatria", "Arritmias, Síncope e Parada Cardiorrespiratória Pediátrica (PALS)", "Arritmias, suporte avançado de vida pediátrico (PALS) e ressuscitação cardiorrespiratória."
        return "Pediatria", "Sepse Pediátrica, Choque e Ressuscitação Hemodinâmica", "Reconhecimento e manejo da sepse pediátrica, choque e suporte hemodinâmico."

    # Congenital Heart Diseases
    if any(k in fn for k in ['cardiopatia congenita', 'tetralogia de fallot', 'crise hipoxica', 'transposicao das grandes arterias', 'comunicacao interatrial', 'cia', 'comunicacao interventricular', 'civ', 'persistencia do canal arterial', 'pca', 'coarctacao de aorta', 'cardiopatia cianogenica', 'cardiopatia acianogenica']):
        return "Pediatria", "Cardiopatias Congênitas Cianogênicas e Acianogênicas", "Diagnóstico e manejo clínico das cardiopatias congênitas acianogênicas e cianogênicas."

    # Vasculitis (Kawasaki & Henoch-Schönlein)
    if any(k in fn for k in ['doenca de kawasaki', 'kawasaki', 'aneurisma de coronaria', 'imunoglobulina venosa em kawasaki', 'purpura de henoch-schonlein', 'vasculite por iga', 'dor abdominal com purpura palpavel em mmii', 'artralgia com purpura']):
        return "Pediatria", "Vasculites na Infância (Henoch-Schönlein e Kawasaki)", "Diagnóstico e tratamento das vasculites mais prevalentes na infância (Kawasaki e Henoch-Schönlein)."

    # Child Safety, Accident Prevention & Abuse
    if any(k in fn for k in ['corpo estranho', 'aspiracao de corpo estranho', 'ingestao de corpo estranho', 'ingestao de moeda', 'ingestao de pilha', 'bateria de botao', 'ingestao de soda caustica', 'esofagite caustica', 'afogamento', 'prevencao de acidentes', 'cadeirinha de carro', 'assento de elevacao', 'maus-tratos', 'abuso fisico', 'abuso sexual infantil', 'sindrome do bebe sacudido', 'fraturas multiplas suspeitas', 'notificacao ao conselho tutelar']):
        return "Pediatria", "Segurança Infantil, Prevenção de Acidentes e Maus-Tratos", "Prevenção de acidentes infantis, aspiração/ingestão de corpos estranhos e abordagem de maus-tratos."

    # Primary Immunodeficiencies, Allergies & Anaphylaxis
    if any(k in fn for k in ['imunodeficiencia primaria', 'imunodeficiencia humoral', 'agamaglobulinemia de bruton', 'imunodeficiencia comum variavel', 'idcv', 'imunodeficiencia combinada grave', 'scid', 'deficiencia de iga', 'deficiencia de complemento', 'doenca granulomatosa cronica', 'anafilaxia', 'adrenalina im', 'alergia alimentar', 'dermatite atopica', 'eczema atopico']):
        return "Pediatria", "Imunodeficiências, Alergias e Anafilaxia na Infância", "Diagnóstico e manejo das imunodeficiências congênitas, alergias e anafilaxia na infância."

    # Medical Genetics, Chromosomopathies & Inborn Errors of Metabolism
    if any(k in fn for k in ['sindrome de down', 'trissomia do 21', 'sindrome de turner', 'sindrome de klinefelter', 'sindrome de edwards', 'sindrome de patau', 'erro inato do metabolismo', 'fenilcetonuria', 'galactosemia', 'mucopolissacaridose', 'fibrose cistica']):
        return "Pediatria", "Genética Médica, Cromossomopatias e Erros Inatos do Metabolismo", "Genética médica, cromossomopatias clássicas e investigação dos erros inatos do metabolismo."

    # =========================================================================
    # Fallback to current subtema if it already matches a valid canonical theme
    # =========================================================================
    if cur_sub in TAX_170.get("Pediatria", []):
        return "Pediatria", cur_sub, f"Classificação clínica baseada no contexto do tema {cur_sub}."
    
    # Fallback
    return "Pediatria", "Puericultura: Marcos do Desenvolvimento (DNPM) e Curvas de Crescimento", "Acompanhamento geral de puericultura e desenvolvimento pediátrico."

if __name__ == "__main__":
    print("Classificador de Pediatria carregado com sucesso.")
