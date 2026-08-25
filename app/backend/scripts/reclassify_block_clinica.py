"""
Classificador de Alta Precisão - Bloco 5: Clínica Médica (44 Subtemas Canônicos)
"""

import sqlite3
import json
import re
import unicodedata
import sys

sys.stdout.reconfigure(encoding="utf-8")

def norm(text):
    text = unicodedata.normalize('NFD', str(text or ''))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().strip()

def match_any(text, patterns):
    for p in patterns:
        if re.search(r'\b' + re.escape(p) + r'\b', text):
            return True
    return False

def classify_clinica(q):
    stem = q.get('stem', '')
    alts = q.get('alternatives', '')
    exp = q.get('explanation', '')
    topic = q.get('topic', '')
    subtema_orig = q.get('subtema_orig', '')
    
    stem_norm = norm(stem)
    topic_norm = norm(topic)
    sub_orig_norm = norm(subtema_orig)
    full_norm = norm(f"{stem} {topic} {subtema_orig}")

    # 1. Síndromes Coronarianas Agudas (Com e Sem Supra de ST)
    if match_any(full_norm, [
        'sindrome coronariana aguda', 'sca', 'iamcsst', 'iamsst', 'infarto agudo do miocardio', 'angina instavel',
        'supradesnivelamento do segmento st', 'troponina ultrassensivel', 'angioplastia coronariana primaria', 'trombolise no iam',
        'dupla antiagregacao plaquetaria coronaria', 'escore timi', 'escore grace', 'clopidogrel no iam', 'ticagrelor'
    ]) or match_any(topic_norm, ['iamcsst (cm)', 'iamsst (cm)', 'sindrome coronariana aguda', 'angina instavel', 'iam', 'coronariana']):
        return "Síndromes Coronarianas Agudas (Com e Sem Supra de ST)", 1.0, "Síndromes coronarianas agudas (IAM com e sem supra de ST, estratificação e terapia de reperfusão)."

    # 2. Insuficiência Cardíaca: Diagnóstico, Estadiamento e Terapia Farmacológica
    if match_any(full_norm, [
        'insuficiencia cardiaca', 'icfer', 'icfep', 'criterios de framingham ic', 'bnp', 'nt-probnp', 'fracao de ejecao reduzida',
        'quadrupla terapia icfer', 'sacubitril-valsartana', 'dapagliflozina na ic', 'empagliflozina na ic', 'espironolactona na ic',
        'edema agudo de pulmao cardiogenico', 'furosemida venosa', 'perfil hemodinamico stevenson'
    ]) or match_any(topic_norm, ['icc', 'insuficiencia cardiaca', 'edema agudo de pulmao', 'cardiologia (cm)', 'icc : alteracoes clinico-laboratoriais']):
        return "Insuficiência Cardíaca: Diagnóstico, Estadiamento e Terapia Farmacológica", 1.0, "Diagnóstico, estadiamento e quatro pilares terapêuticos modificadores de mortalidade na IC."

    # 3. Taquiarritmias, Bradiarritmias, Síncope e Suporte Avançado (ACLS)
    if match_any(full_norm, [
        'fibrilacao atrial', 'flutter atrial', 'cha2ds2-vasc', 'anticoagulacao na fa', 'doac', 'varfarina', 'taquicardia supraventricular',
        'tsv paroxistica', 'manobra vagal', 'adenosina iv', 'taquicardia ventricular', 'fibrilacao ventricular', 'pcr no adulto',
        'acls', 'ritmos chocaveis', 'ritmos nao chocaveis', 'atividade eletrica sem pulso', 'aesp', 'assistolia', 'bloqueio atrioventricular',
        'bav de 1o grau', 'bav de 2o grau mobitz i', 'bav de 2o grau mobitz ii', 'bav total', 'bavt', 'marcapasso provisorio', 'atropina na bradicardia'
    ]) or match_any(topic_norm, ['arritmias', 'fibrilacao atrial', 'acls', 'pcr adulto', 'bradiarritmias', 'taquiarritmias', 'taquiarritmia (ped)', 'sincope (cm)']):
        return "Taquiarritmias, Bradiarritmias, Síncope e Suporte Avançado (ACLS)", 1.0, "Manejo de arritmias cardíacas, protocolo ACLS na parada cardiorrespiratória e estratificação de síncope."

    # 4. Hipertensão Arterial Sistêmica e Crises Hipertensivas
    if match_any(full_norm, [
        'hipertensao arterial sistemica', 'has resistente', 'mapa 24 horas', 'mrpa', 'emergencia hipertensiva',
        'urgencia hipertensiva', 'encefalopatia hipertensiva', 'nitroprussiato de sodio', 'labetalol', 'hipertensao secundaria',
        'hiperaldosteronismo primario', 'feocromocitoma', 'estenose de arteria renal'
    ]) or match_any(topic_norm, ['has', 'hipertensao arterial', 'crise hipertensiva', 'emergencia hipertensiva', 'has (cm)']):
        return "Hipertensão Arterial Sistêmica e Crises Hipertensivas", 1.0, "Diretrizes de HAS, metas pressóricas, hipertensão secundária e emergências hipertensivas."

    # 5. Valvopatias Adquiridas e Miocardiopatias
    if match_any(full_norm, [
        'estenose aortica', 'insuficiencia mitral', 'estenose mitral', 'insuficiencia aortica', 'valva aortica bicuspide',
        'sopro holossistolico', 'sopro ejetivo aortico', 'pulso parvus et tardus', 'miocardiopatia hipertrofica',
        'miocardiopatia dilatada', 'miocardiopatia periparto', 'miocardite'
    ]) or match_any(topic_norm, ['valvopatias', 'estenose aortica', 'insuficiencia mitral', 'miocardiopatias', 'valvopatias adquiridas']):
        return "Valvopatias Adquiridas e Miocardiopatias", 1.0, "Avaliação clínica, ecocardiográfica e propedêutica das valvopatias adquiridas e miocardiopatias."

    # 6. Dislipidemias, Síndrome Metabólica e Risco Cardiovascular
    if match_any(full_norm, [
        'dislipidemia', 'estatinas de alta potencia', 'atorvastatina 80', 'rosuvastatina 20', 'ezetimiba', 'meta de ldl-c',
        'escore de risco global de framingham', 'sindrome metabolica', 'hipertrigliceridemia grave', 'fenofibrato'
    ]) or match_any(topic_norm, ['dislipidemia', 'dislipidemias', 'sindrome metabolica', 'risco cardiovascular', 'dislipidemias (cm)']):
        return "Dislipidemias, Síndrome Metabólica e Risco Cardiovascular", 1.0, "Estratificação de risco cardiovascular, metas de lípides e farmacoterapia com estatinas."

    # 7. Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento
    if match_any(full_norm, [
        'diabetes mellitus tipo 2', 'dm2', 'diabetes mellitus tipo 1', 'dm1', 'hemoglobina glicada', 'hba1c',
        'metformina', 'inibidor de sglt2', 'isglt2', 'agonista de glp-1', 'glp1', 'insulinas nph e regular', 'esquema basal-bolus',
        'cetoacidose diabetica', 'cad', 'estado hiperglicemico hiperosmolar', 'ehh', 'reponte de potassio na cetoacidose',
        'neuropatia diabetica', 'retinopatia diabetica', 'pe diabetico'
    ]) or match_any(topic_norm, ['diabetes', 'cetoacidose diabetica (cm)', 'cetoacidose', 'pe diabetico', 'insulina', 'diabetes mellitus']):
        return "Diabetes Mellitus: Metas Glicêmicas, Complicações e Tratamento", 1.0, "Manejo ambulatorial do DM, metas de HbA1c e emergências hiperglicêmicas agudas (CAD e EHH)."

    # 8. Hipotireoidismo, Hipertireoidismo e Nódulos Tireoidianos
    if match_any(full_norm, [
        'hipotireoidismo primario', 'tireoidite de hashimoto', 'levotiroxina', 'tsh elevado e t4 livre baixo',
        'hipertireoidismo', 'doenca de graves', 'exoftalmia', 'metimazol', 'propiltiouracil', 'ptu', 'crise tireotoxica',
        'tempestade tireoidiana', 'tireoidite subaguda de de quervain', 'hipotireoidismo subclinico', 'nodulos tireoideanos'
    ]) or match_any(topic_norm, ['tireoide', 'hipotireoidismo', 'hipertireoidismo', 'doenca de graves', 'nodulos tireoideanos (cm)', 'tireoidites']):
        return "Hipotireoidismo, Hipertireoidismo e Nódulos Tireoidianos", 1.0, "Disfunções tireoidianas (Hipotireoidismo, Doença de Graves, Tireoidites e Crise Tireotóxica)."

    # 9. Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio
    if match_any(full_norm, [
        'insuficiencia adrenal primaria', 'doenca de addison', 'crise adrenal aguda', 'hidrocortisona venosa',
        'sindrome de cushing', 'hipercortisolismo', 'teste de supressao com dexametasona', 'hiperparatireoidismo primario',
        'hipercalcemia maligna', 'crise hipercalcemica', 'acido zoledronico', 'hipocalcemia', 'sinal de chvostek', 'sinal de trousseau'
    ]) or match_any(topic_norm, ['adrenal', 'suprarrenal', 'paratireoide', 'hipercalcemia', 'cushing', 'addison', 'disturbios do calcio']):
        return "Doenças da Suprarrenal, Paratireoides e Distúrbios do Cálcio", 1.0, "Patologias da suprarrenal, hiper/hipoparatireoidismo e distúrbios agudos do metabolismo do cálcio."

    # 10. Asma e Doença Pulmonar Obstrutiva Crônica (DPOC)
    if match_any(full_norm, [
        'dpoc', 'doenca pulmonar obstrutiva cronica', 'espirometria vef1/cvf < 0,70', 'gold a gold b gold e',
        'exacerbacao aguda de dpoc', 'antibiotico na exacerbacao de dpoc', 'corticoide sistemico no dpoc', 'lama laba ics',
        'oxigenoterapia domiciliar prolongada', 'asma no adulto', 'gina etapas', 'corticoide inalatorio e formoterol'
    ]) or match_any(topic_norm, ['dpoc', 'asma adulto', 'espirometria', 'pneumologia (cm)', 'asma (cm)']):
        return "Asma e Doença Pulmonar Obstrutiva Crônica (DPOC)", 1.0, "Manejo da Asma e DPOC conforme diretrizes GINA/GOLD e tratamento das exacerbações."

    # 11. Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas
    if match_any(full_norm, [
        'pneumonia adquirida na comunidade', 'pac no adulto', 'escore curb-65', 'escore psi', 'pneumonia grave',
        'streptococcus pneumoniae pac', 'amoxicilina e clavulanato com macrolideo', 'ceftriaxona e azitromicina',
        'pneumonia por aspiracao', 'abscesso pulmonar clinico', 'derrame pleural parapneumonico', 'covid', 'covid-19', 'sars-cov-2'
    ]) or match_any(topic_norm, ['pac', 'pneumonia adquirida na comunidade', 'curb-65', 'covid (cm)', 'derrame pleural (cm)', 'derrame pleural (cir)']):
        return "Pneumonia Adquirida na Comunidade (PAC) e Síndromes Respiratórias Agudas", 1.0, "Diagnóstico, estratificação de gravidade (CURB-65) e antibioticoterapia na PAC do adulto."

    # 12. Tromboembolismo Pulmonar (TEP) e Hipertensão Pulmonar
    if match_any(full_norm, [
        'tromboembolismo pulmonar', 'tep no adulto', 'escore de wells tep', 'escore de geneva', 'dimero-d',
        'angiotomografia de arterias pulmonares', 'tep de alto risco com choque', 'trombolise no tep', 'alteplase tep',
        'anticoagulacao no tep', 'hipertensao pulmonar grupo 1 a 5'
    ]) or match_any(topic_norm, ['tep', 'tromboembolismo pulmonar', 'hipertensao pulmonar', 'tep (cm)']):
        return "Tromboembolismo Pulmonar (TEP) e Hipertensão Pulmonar", 1.0, "Estratificação diagnóstica, escore de Wells e terapia anticoagulante/trombolítica no TEP."

    # 13. Ventilação Mecânica, SARA e Insuficiência Respiratória Aguda
    if match_any(full_norm, [
        'ventilacao mecanica invasiva', 'sara', 'sindrome do desconforto respiratorio agudo', 'relacao pao2/fio2',
        'criterios de berlim sara', 'ventilacao protetora', 'volume corrente 6 ml/kg peso predito', 'pressao de plato < 30',
        'driving pressure', 'pressao de distensao', 'posicao prona na sara', 'sequencia rapida de intubacao', 'etomidato na intubacao', 'usg pocus'
    ]) or match_any(topic_norm, ['ventilacao mecanica', 'sara', 'intubacao', 'usg pocus', 'via aérea e intubação (cm)', 'via aerea e intubacao (cm)']):
        return "Ventilação Mecânica, SARA e Insuficiência Respiratória Aguda", 1.0, "Parâmetros de ventilação mecânica protetora, critérios de Berlim na SARA e IOT."

    # 14. Doenças Pulmonares Intersticiais e Fibrose Pulmonar
    if match_any(full_norm, [
        'fibrose pulmonar idiopatica', 'padrao de pneumonia intersticial usual', 'piu', 'faveolamento na tc de torax',
        'sarcoidose pulmonar', 'linfadenopatia hilar bilateral', 'pneumonite por hipersensibilidade'
    ]) or match_any(topic_norm, ['doencas intersticiais', 'fibrose pulmonar', 'sarcoidose', 'doencas pulmonares intersticiais']):
        return "Doenças Pulmonares Intersticiais e Fibrose Pulmonar", 1.0, "Doenças pulmonares difusas parenquimatosas, sarcoidose e padrão PIU."

    # 15. Tuberculose Pulmonar e Extrapulmonar: Diagnóstico e Manejo
    if match_any(full_norm, [
        'tuberculose pulmonar', 'baciloscopia de escarro', 'teste rapido molecular para tuberculose', 'trm-tb',
        'esquema ripe', 'rifampicina isoniazida pirazinamida etambutol', 'infeccao latente por tuberculose', 'iltb',
        'prova tuberculinica', 'ppd reator', 'igra', 'tuberculose pleural', 'tuberculose meningoencefalica'
    ]) or match_any(topic_norm, ['tuberculose', 'tb', 'ripe', 'iltb', 'tuberculose (cm)']):
        return "Tuberculose Pulmonar e Extrapulmonar: Diagnóstico e Manejo", 1.0, "Diagnóstico microbiológico/molecular, esquema RIPE e tratamento de infecção latente (ILTB)."

    # 16. Infecção pelo HIV: Diagnóstico, TARV e Infecções Oportunistas
    if match_any(full_norm, [
        'infeccao pelo hiv', 'tarv', 'dolutegravir tenofovir lamivudina', 'contagem de linfocitos t cd4',
        'pneumocistose', 'pneumocystis jirovecii', 'sulfametoxazol-trimetoprima profilaxia', 'neurotoxoplasmose no hiv',
        'neurocriptococose', 'sarcoma de kaposi', 'prep hiv', 'pep hiv'
    ]) or match_any(topic_norm, ['hiv', 'tarv', 'aids', 'oportunistas hiv', 'infeccao pelo hiv (cm)']):
        return "Infecção pelo HIV: Diagnóstico, TARV e Infecções Oportunistas", 1.0, "Diagnóstico, esquemas antirretrovirais de primeira linha (TARV) e infecções oportunistas definidoras."

    # 17. Síndromes Febris Agudas e Arboviroses
    if match_any(full_norm, [
        'dengue', 'classificacao de dengue a b c d', 'sinais de alarme da dengue', 'prova do laco', 'hidratacao venosa na dengue',
        'chikungunya', 'artralgia cronica por chikungunya', 'zika virus', 'febre amarela', 'leptospirose', 'sindrome de weil',
        'malaria', 'plasmodium vivax', 'plasmodium falciparum', 'gota espessa'
    ]) or match_any(topic_norm, ['dengue', 'arboviroses', 'chikungunya', 'zika', 'febre amarela', 'malaria', 'leptospirose', 'dengue (cm)']):
        return "Síndromes Febris Agudas e Arboviroses (Dengue, Chikungunya, Febre Amarela)", 1.0, "Manejo clínico de arboviroses (Dengue e sinais de alarme), leptospirose e malária."

    # 18. Meningites, Encefalites e Infecções do SNC
    if match_any(full_norm, [
        'meningite bacteriana aguda', 'meningite meningococica', 'quimioprofilaxia para contatos de meningite',
        'rifampicina profilaxia meningococo', 'ceftriaxona e vancomicina meningite', 'dexametasona na meningite bacteriana',
        'analise do liquor', 'pleocitose neutrofilica liquor', 'encefalite herpetica', 'aciclovir venoso encefalite', 'meningoencefalite'
    ]) or match_any(topic_norm, ['meningite', 'encefalite', 'liquor', 'infeccoes do snc', 'meningoencefalite herpetica (cm)']):
        return "Meningites, Encefalites e Infecções do SNC", 1.0, "Diagnóstico liquórico, antibioticoterapia empírica e profilaxia de contatos nas meningites/encefalites."

    # 19. Hepatites Virais (A, B, C) e Icterícias Metabólicas
    if match_any(full_norm, [
        'hepatite b', 'hbsag', 'anti-hbs', 'anti-hbc igm', 'anti-hbc igg', 'hbeag', 'anti-hbe', 'tenofovir na hepatite b',
        'hepatite c', 'anti-hcv', 'hcv-rna', 'antivirais de acao direta sofosbuvir velpatasvir', 'hepatite a',
        'sindrome de gilbert', 'hiperbilirrubinemia indireta isolada'
    ]) or match_any(topic_norm, ['hepatite b', 'hepatite c', 'hepatites virais', 'gilbert', 'hepatite (cm)']):
        return "Hepatites Virais (A, B, C) e Icterícias Metabólicas", 1.0, "Sorologia da Hepatite B, tratamento da Hepatite C crônica e icterícias metabólicas."

    # 20. Endocardite Infecciosa e Sepse de Foco Endovascular
    if match_any(full_norm, [
        'endocardite infecciosa', 'criterios de duke modificados', 'staphylococcus aureus endocardite',
        'streptococcus viridans', 'hemoculturas seriadas endocardite', 'ecocardiograma transesofagico endocardite',
        'vegetacao valvar', 'profilaxia antibiotica para endocardite infecciosa'
    ]) or match_any(topic_norm, ['endocardite infecciosa', 'endocardite', 'criterios de duke']):
        return "Endocardite Infecciosa e Sepse de Foco Endovascular", 1.0, "Critérios de Duke, agentes microbiológicos e profilaxia de endocardite infecciosa."

    # 21. Celulite, Erisipela, Osteomielite e Infecções de Partes Moles
    if match_any(full_norm, [
        'erisipela', 'celulite infecciosa', 'osteomielite no adulto', 'artrite septica no adulto',
        'puncao articular com liquido turvo', 'cefalexina erisipela', 'oxacilina', 'antibioticos: situacoes clinicas'
    ]) or match_any(topic_norm, ['erisipela', 'celulite', 'osteomielite', 'artrite septica', 'antibióticos: situações clínicas (cm)', 'antibioticos: situacoes clinicas (cm)']):
        return "Celulite, Erisipela, Osteomielite e Infecções de Partes Moles", 1.0, "Diagnóstico diferencial entre erisipela/celulite e infecções ósseas/articulares."

    # 22. Infecções Sexualmente Transmissíveis (ISTs) no Adulto
    if match_any(full_norm, [
        'uretrite gonococica', 'uretrite nao gonococica', 'ceftriaxona e azitromicina uretrite', 'neisseria gonorrhoeae',
        'chlamydia trachomatis', 'sifilis primaria', 'sifilis secundaria', 'sifilis latente', 'penicilina benzatina na sifilis'
    ]) or match_any(topic_norm, ['ists no adulto', 'uretrite', 'sifilis adulto', 'ists (cm)']):
        return "Infecções Sexualmente Transmissíveis (ISTs) no Adulto", 1.0, "Abordagem sindrômica de corrimento uretral e sífilis no adulto."

    # 23. Dermatoses Infecciosas, Hanseníase e Leishmanioses
    if match_any(full_norm, [
        'hanseniase', 'paucibacilar', 'multibacilar', 'poliquimioterapia hanseniase', 'rifampicina dapsona clofazimina',
        'reacao hansenica tipo 1', 'reacao hansenica tipo 2', 'eritema nodoso hansenico', 'talidomida reacao',
        'leishmaniose tegumentar americana', 'leishmaniose visceral', 'calazar', 'antimoniato de meglumina', 'anfotericina b lipossomal calazar'
    ]) or match_any(topic_norm, ['hanseniase', 'leishmaniose', 'calazar', 'dermatoses infecciosas']):
        return "Dermatoses Infecciosas, Hanseníase e Leishmanioses", 1.0, "Classificação operacional da hanseníase, reações hansênicas e leishmanioses."

    # 24. Dermatologia Clínica: Farmacodermias Graves, Eczemas e Psoríase
    if match_any(full_norm, [
        'farmacodermia', 'sindrome de stevens-johnson', 'ssj', 'necrolise epidermica toxica', 'net', 'sindrome dress',
        'psoriase em placas', 'artrite psoriasica', 'dermatite atopica no adulto', 'eczema de contato', 'penfigo vulgar', 'penfigoide bolhoso'
    ]) or match_any(topic_norm, ['dermatologia', 'farmacodermia', 'psoriase', 'stevens-johnson', 'urticaria (cm)', 'alergias (cm)']):
        return "Dermatologia Clínica: Farmacodermias Graves, Eczemas e Psoríase", 1.0, "Farmacodermias graves com descolamento epidérmico e dermatoses inflamatórias crônicas."

    # 25. Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática
    if match_any(full_norm, [
        'cirrose hepatica', 'hipertensao portal', 'ascite cirrotica', 'paracentese diagnostica', 'gasa > 1,1',
        'peritonite bacteriana espontanea', 'pbe', 'cefotaxima pbe', 'albumina na pbe', 'profilaxia secundaria pbe',
        'encefalopatia hepatica', 'lactulose', 'escore child-pugh', 'escore meld', 'hda varicosa', 'terlipressina hda varicosa', 'ligadura elastica de varizes',
        'diarreias agudas e clostridium', 'pancreas e vias biliares'
    ]) or match_any(topic_norm, ['cirrose', 'hipertensao portal', 'ascite', 'pbe', 'encefalopatia hepatica', 'hda varicosa (cm)', 'diarréias agudas e clostridium (cm)', 'pâncreas e vias biliares']):
        return "Cirrose Hepática, Hipertensão Portal e Insuficiência Hepática", 1.0, "Complicações da hipertensão portal (Ascite, PBE, Encefalopatia, Hemorragia varicosa) e escores Child/MELD."

    # 26. Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)
    if match_any(full_norm, [
        'injuria renal aguda', 'ira prerenal', 'ira renal', 'ira pos-renal', 'criterios kdigo ira', 'necrose tubular aguda',
        'fracao de excrecao de sodio < 1%', 'fena', 'doenca renal cronica', 'drc', 'estadiamento kdigo drc',
        'taxa de filtracao glomerular', 'indicações de hemodialise de urgencia', 'hipercalemia refrataria dialise'
    ]) or match_any(topic_norm, ['ira', 'drc', 'injuria renal aguda', 'doenca renal cronica', 'nefrologia (cm)']):
        return "Injúria Renal Aguda (IRA) e Doença Renal Crônica (DRC)", 1.0, "Classificação KDIGO para IRA/DRC, diagnóstico diferencial de NTA e hemodiálise de urgência."

    # 27. Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias
    if match_any(full_norm, [
        'sindrome nefritica', 'glomerulonefrite difusa aguda', 'gnda', 'gnpe', 'queda transitoria do complemento c3',
        'hematuria dismorfica', 'cilindros hematicos', 'sindrome nefrotica no adulto', 'proteinuria macica > 3,5 g/dia',
        'glomerulopatia membranosa', 'gess', 'nefropatia por iga', 'doenca de berger'
    ]) or match_any(topic_norm, ['sindrome nefritica', 'sindrome nefrotica', 'glomerulopatias', 'nefropatia por iga']):
        return "Síndromes Glomerulares: Nefrítica, Nefrótica e Tubulopatias", 1.0, "Propedêutica das glomerulopatias primárias e secundárias do adulto."

    # 28. Distúrbios Eletrolíticos e Equilíbrio Ácido-Base
    if match_any(full_norm, [
        'hiponatremia', 'sindrome da secrecao inapropriada de adh', 'siadh', 'mielinolise pontina central',
        'hipernatremia', 'hipercalemia', 'gluconato de calcio estabilizacao de membrana', 'solucao polarizante insulina e glicose',
        'hipocalemia', 'gasometria arterial', 'acidose metabolica com anion gap elevado', 'alcalose metabolica'
    ]) or match_any(topic_norm, ['disturbios eletroliticos', 'gasometria', 'hiponatremia (cm)', 'hipercalemia', 'acido-base', 'distúrbios hidroeletrolíticos (cm)']):
        return "Distúrbios Eletrolíticos (Sódio, Potássio) e Equilíbrio Ácido-Base", 1.0, "Correção segura de hipo/hipernatremia, manejo da hipercalemia grave e interpretação de gasometria."

    # 29. Acidente Vascular Cerebral Isquêmico e Hemorrágico (Janela de Trombólise)
    if match_any(full_norm, [
        'acidente vascular cerebral', 'avc isquemico', 'avci', 'janela de trombolise 4,5 horas', 'alteplase avci',
        'tenecteplase', 'trombectomia mecanica', 'escala nihss', 'avc hemorragico', 'hemorragia subaracnoidea',
        'hsa', 'aneurisma cerebral roto', 'nimodipino hsa'
    ]) or match_any(topic_norm, ['avc', 'avc isquemico (cm)', 'avc hemorragico', 'trombolise avc']):
        return "Acidente Vascular Cerebral Isquêmico e Hemorrágico (Janela de Trombólise)", 1.0, "Protocolo agudo de AVC isquêmico, critérios de trombólise endovenosa e hemorragia subaracnóidea."

    # 30. Cefaleias Primárias e Secundárias de Alarme
    if match_any(full_norm, [
        'enxaqueca', 'migranea', 'cefaleia tensional', 'cefaleia em salvas', 'sinais de alarme para cefaleia secundaria',
        'red flags cefaleia', 'arterite de celulas gigantes', 'arterite temporal e vhs elevado'
    ]) or match_any(topic_norm, ['cefaleia', 'enxaqueca', 'cefaleias primarias']):
        return "Cefaleias Primárias (Enxaqueca, Tensional) e Secundárias de Alarme", 1.0, "Tratamento agudo e profilático das cefaleias primárias e reconhecimento de sinais de alarme."

    # 31. Neuropatias Periféricas, Miastenia Gravis e Doenças Neuromusculares
    if match_any(full_norm, [
        'sindrome de guillain-barre', 'paralisia flacida ascendente', 'dissociacao albuminocitologica no liquor',
        'imunoglobulina venosa guillain barre', 'miastenia gravis', 'anticorpo anti-receptor de acetilcolina',
        'piridostigmina', 'crise miastenica', 'esclerose lateral amiotrofica', 'ela', 'polineuropatia periferica',
        'vertigem', 'tontura'
    ]) or match_any(topic_norm, ['guillain-barre', 'miastenia gravis', 'neuropatias perifericas', 'doencas neuromusculares', 'vertigem (cm)', 'síndrome de guillain barré e suas variantes (ped)']):
        return "Neuropatias Periféricas, Miastenia Gravis e Doenças Neuromusculares", 1.0, "Diagnóstico e condutas na Síndrome de Guillain-Barré, Miastenia Gravis e neuropatias."

    # 32. Neurointensivismo, Morte Encefálica e Cuidados Críticos
    if match_any(full_norm, [
        'protocolo de morte encefalica', 'criterios de morte encefalica resolucao cfm', 'dois exames clinicos teste de apneia',
        'exame grafico complementar morte encefalica', 'doador de orgaos manutencao hemodinamica'
    ]) or match_any(topic_norm, ['morte encefalica', 'neurointensivismo']):
        return "Neurointensivismo, Morte Encefálica e Cuidados Críticos", 1.0, "Protocolo de determinação de morte encefálica e manejo hemodinâmico do potencial doador."

    # 33. Diagnóstico Diferencial das Anemias e Hemoglobinopatias
    if match_any(full_norm, [
        'anemia ferropriva no adulto', 'anemia de doenca cronica', 'anemia megaloblastica', 'deficiencia de vitamina b12',
        'anemia perniciosa', 'anemia falciforme', 'crise dolorosa vaso-oclusiva', 'sindrome toracica aguda falciforme',
        'talassemia minor', 'talassemia major', 'anemia hemolitica autoimune', 'teste de coomb direto positivo', 'talassemia'
    ]) or match_any(topic_norm, ['anemia', 'anemias', 'anemia falciforme', 'anemia ferropriva', 'talassemia (ped)']):
        return "Diagnóstico Diferencial das Anemias e Hemoglobinopatias", 1.0, "Diagnóstico diferencial laboratorial das anemias micro, normo e macrocíticas e doença falciforme."

    # 34. Leucemias, Linfomas e Mieloma Múltiplo
    if match_any(full_norm, [
        'leucemia mieloide aguda', 'lma', 'bastonetes de auer', 'leucemia mieloide cronica', 'lmc', 'cromossomo filadelfia',
        'imatinibe', 'leucemia linfoide aguda', 'lla', 'linfoma de hodgkin', 'celulas de reed-sternberg',
        'linfoma nao-hodgkin', 'mieloma multiplo', 'criterios crab', 'gamopatia monoclonal', 'pico monoclonal eletroforese',
        'emergencias oncologicas'
    ]) or match_any(topic_norm, ['leucemia', 'linfoma', 'mieloma multiplo', 'hematologia', 'gamopatia monoclonal de significado indeterminado (gmsi) (cm)', 'emergências oncológicas (cm)']):
        return "Leucemias, Linfomas e Mieloma Múltiplo", 1.0, "Neoplasias hematológicas (Leucemias agudas/crônicas, Linfomas e Mieloma Múltiplo)."

    # 35. Coagulopatias, Trombofilias, Púrpuras e Hemoterapia
    if match_any(full_norm, [
        'purpura trombocitopenica imune', 'pti', 'purpura trombocitopenica trombotica', 'ptt', 'plasmaferese de urgencia ptt',
        'adamts13', 'coagulacao intravascular disseminada', 'civd', 'hemofilia a', 'fator viii', 'trombofilia', 'transfusao de concentrado de hemacias',
        'transfusao de plaquetas', 'reacao transfusional'
    ]) or match_any(topic_norm, ['coagulopatias', 'trombofilia', 'hemoterapia', 'pti', 'ptt']):
        return "Coagulopatias, Trombofilias, Púrpuras e Hemoterapia", 1.0, "Distúrbios da hemostasia primária/secundária, púrpuras e indicações de hemotransfusão."

    # 36. Lúpus Eritematoso Sistêmico (LES), Esclerose Sistêmica e Miopatias Inflamatórias
    if match_any(full_norm, [
        'lupus eritematoso sistemico', 'les', 'anticorpo anti-dna dupla helice', 'anti-sm', 'nefrite lupica',
        'hidroxicloroquina no lupus', 'esclerose sistemica', 'esclerodermia', 'fenomeno de raynaud', 'esclerose sistemica limitada crest',
        'anticorpo anti-centromero', 'anti-scl70', 'dermatomiosite', 'polimiosite', 'heliotropo', 'papulas de gottron'
    ]) or match_any(topic_norm, ['lupus', 'les', 'esclerose sistemica', 'dermatomiosite', 'reumatologia (cm)']):
        return "Lúpus Eritematoso Sistêmico (LES), Esclerose Sistêmica e Miopatias Inflamatórias", 1.0, "Critérios diagnósticos e autoanticorpos do LES, Esclerose Sistêmica e Miopatias."

    # 37. Artrite Reumatoide, Espondiloartrites e Artrites Microcristalinas
    if match_any(full_norm, [
        'artrite reumatoide', 'poliartrite simetrica de pequenas articulacoes', 'fator reumatoide', 'anti-ccp',
        'metotrexato na ar', 'espondilite anquilosante', 'hla-b27', 'gota aguda', 'cristais de urato monossodico birrefringencia negativa',
        'colchicina na crise de gota', 'alopurinol', 'artrite por pirofosfato de calcio pseudogota', 'espondiloartrites'
    ]) or match_any(topic_norm, ['artrite reumatoide', 'gota', 'espondilite', 'artrites', 'espondiloartrites (cm)']):
        return "Artrite Reumatoide, Espondiloartrites e Artrites Microcristalinas", 1.0, "Propedêutica e manejo da Artrite Reumatoide, Espondiloartrites e Artrites Microcristalinas (Gota)."

    # 38. Vasculites Sistêmicas dos Grandes, Médios e Pequenos Vasos
    if match_any(full_norm, [
        'arterite de takayasu', 'arterite de celulas gigantes temporal', 'poliarterite nodosa', 'pan',
        'granulomatose com poliangeite', 'wegener', 'c-anca', 'poliangeite microscopica', 'p-anca',
        'granulomatose eosinofilica com poliangeite', 'churg-strauss'
    ]) or match_any(topic_norm, ['vasculites sistemicas', 'takayasu', 'wegener', 'arterite temporal']):
        return "Vasculites Sistêmicas dos Grandes, Médios e Pequenos Vasos", 1.0, "Classificação de Chapel Hill e quadro clínico das vasculites de grandes, médios e pequenos vasos."

    # 39. Sepse no Adulto, Choque Séptico e Ressuscitação Hemodinâmica
    if match_any(full_norm, [
        'sepse no adulto', 'choque septico', 'criterios qsofa', 'criterios sofa sepse', 'pacote de 1 hora da sepse',
        'expansao volêmica 30 ml/kg cristaloide', 'noradrenalina vasopressor de escolha', 'lactato serico seriado na sepse',
        'culturas antes do antibiotico de amplo espectro'
    ]) or match_any(topic_norm, ['sepse no adulto', 'choque septico', 'sepse (cm)']):
        return "Sepse no Adulto, Choque Séptico e Ressuscitação Hemodinâmica", 1.0, "Definição de Sepsis-3, bundle de 1 hora e ressuscitação com cristaloides e noradrenalina."

    # 40. Toxicologia Clínica e Acidentes por Animais Peçonhentos
    if match_any(full_norm, [
        'intoxicacao exogena aguda', 'sindrome colinergica', 'intoxicacao por organofosforados carbamatos', 'atropina e pralidoxima',
        'sindrome anticolinergica', 'sindrome opioide', 'naloxona', 'intoxicacao por paracetamol', 'n-acetilcisteina',
        'acidente botropico', 'jararaca', 'acidente crotalico', 'cascavel', 'acidente laquetico', 'surucucu',
        'acidente elapidico', 'coral verdadeira', 'acidente escorpionico', 'tityus serrulatus', 'soro antiescorpionico', 'acidente loxoscelico aranha marrom'
    ]) or match_any(topic_norm, ['toxicologia', 'animais peconhentos', 'intoxicacao exogena', 'acidentes por animais', 'intoxicações (cm)', 'escorpião (ped)']):
        return "Toxicologia Clínica e Acidentes por Animais Peçonhentos", 1.0, "Toxíndromes agudas, antídotos específicos e manejo de envenenamentos por animais peçonhentos."

    # 41. Psiquiatria: Transtornos do Humor, Ansiedade e Psicoses
    if match_any(full_norm, [
        'transtorno depressivo maior', 'isrs', 'sertralina', 'escitalopram', 'transtorno afetivo bipolar', 'mania',
        'carbonato de litio', 'acido valproico', 'esquizofrenia', 'antipsicoticos atipicos', 'quetiapina', 'olanzapina',
        'risperidona', 'transtorno de panico', 'transtorno de ansiedade generalizada', 'tag', 'risco de suicidio'
    ]) or match_any(topic_norm, ['psiquiatria', 'depressao', 'transtorno bipolar', 'esquizofrenia', 'ansiedade', 'transtorno de pânico (cm)', 'insônia e distúrbios do sono (cm)', 'transtorno de panico (cm)']):
        return "Psiquiatria: Transtornos do Humor, Ansiedade e Psicoses", 1.0, "Transtornos do humor (Depressão e Bipolaridade), Psicoses, Ansiedade e psicofarmacologia."

    # 42. Transtornos por Uso de Substâncias (Álcool, Tabaco e Drogas de Abuso)
    if match_any(full_norm, [
        'sindrome de abstinencia alcoolica', 'delirium tremens', 'diazepam na abstinencia', 'escala ciwa-ar',
        'encefalopatia de wernicke', 'tiamina vitamina b1 antes da glicose', 'cessacao do tabagismo', 'bupropiona', 'vareniclina',
        'intoxicacao por cocaina e crack', 'antagonistas opioides'
    ]) or match_any(topic_norm, ['alcoolismo', 'tabagismo', 'drogas de abuso', 'abstinencia alcoolica', 'abuso de substâncias e psicose (cm)', 'transtornos por uso de substâncias']):
        return "Transtornos por Uso de Substâncias (Álcool, Tabaco e Drogas de Abuso)", 1.0, "Abstinência alcoólica, Encefalopatia de Wernicke e cessação do tabagismo."

    # 43. Políticas de Saúde Mental e Atenção Psicossocial (CAPS)
    if match_any(full_norm, [
        'reforma psiquiatrica lei 10.216', 'centro de atencao psicossocial', 'caps i', 'caps ii', 'caps iii', 'caps ad', 'capsij',
        'leitos de atencao integral a saude mental', 'desinstitucionalizacao psiquiatrica', 'matriciamento em saude mental'
    ]) or match_any(topic_norm, ['caps', 'reforma psiquiatrica', 'saude mental coletiva', 'politicas de saude mental']):
        return "Políticas de Saúde Mental e Atenção Psicossocial (CAPS)", 1.0, "Rede de Atenção Psicossocial (RAPS), tipos de CAPS e diretrizes da Lei 10.216."

    # 44. Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas
    return "Geriatria: Avaliação Ampla do Idoso, Síndromes Demenciais e Quedas", 0.95, "Avaliação geriátrica ampla, polifarmácia, síndromes demenciais (Alzheimer, Vascular, Corpos de Lewy) e prevenção de quedas."

def process_block5(apply=False):
    conn = sqlite3.connect("app/backend/medquest.db")
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT q.id, q.stem, q.topic, q.subtema_orig, q.area, q.subtema, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.area = 'Clínica Médica'
        ORDER BY q.id
    """).fetchall()
    
    print(f"==================================================")
    print(f"PROCESSANDO BLOCO 5: CLÍNICA MÉDICA ({len(rows)} QUESTÕES)")
    print(f"Modo: {'APLICAÇÃO DIRETA NO BANCO' if apply else 'AUDITORIA / SIMULAÇÃO'}")
    print(f"==================================================")
    
    changes = []
    distribution = {}
    
    for r in rows:
        qid = r["id"]
        old_sub = r["subtema"]
        
        q_dict = {
            "id": qid,
            "stem": r["stem"] or "",
            "topic": r["topic"] or "",
            "subtema_orig": r["subtema_orig"] or "",
            "area": r["area"] or "",
            "subtema": r["subtema"] or "",
            "explanation": r["explanation_text"] or "",
        }
        
        new_sub, conf, rationale = classify_clinica(q_dict)
        distribution[new_sub] = distribution.get(new_sub, 0) + 1
        
        if old_sub != new_sub:
            changes.append({
                "id": qid,
                "old_subtema": old_sub,
                "new_subtema": new_sub,
                "confidence": conf,
                "rationale": rationale
            })
            
    print(f"\nTotal de reclassificações no Bloco 5: {len(changes)} ({len(changes)/len(rows)*100:.1f}%)")
    print(f"\n--- DISTRIBUIÇÃO DOS 44 SUBTEMAS DO BLOCO 5 ---")
    for s, cnt in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {s}: {cnt} questões")
        
    if apply and changes:
        with conn:
            for ch in changes:
                conn.execute("""
                    UPDATE questions 
                    SET subtema = ?,
                        subtema_orig = CASE WHEN subtema_orig IS NULL OR subtema_orig = '' THEN subtema ELSE subtema_orig END
                    WHERE id = ?
                """, (ch["new_subtema"], ch["id"]))
        print(f"\n✅ {len(changes)} questões do Bloco 5 atualizadas no banco com sucesso!")
        
    return changes

if __name__ == "__main__":
    apply_flag = "--apply" in sys.argv
    process_block5(apply=apply_flag)
