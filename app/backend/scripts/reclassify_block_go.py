"""
Classificador de Alta Precisão - Bloco 3: Ginecologia e Obstetrícia (37 Subtemas Canônicos)
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

def classify_go(q):
    stem = q.get('stem', '')
    alts = q.get('alternatives', '')
    exp = q.get('explanation', '')
    topic = q.get('topic', '')
    subtema_orig = q.get('subtema_orig', '')
    
    stem_norm = norm(stem)
    topic_norm = norm(topic)
    sub_orig_norm = norm(subtema_orig)
    full_norm = norm(f"{stem} {topic} {subtema_orig}")

    # 1. Hemorragias da Primeira Metade: Abortamento, Ectópica e Mola
    if match_any(full_norm, [
        'abortamento', 'aborto retido', 'aborto incompleto', 'aborto inevitavel', 'ameu', 'curetagem uterina',
        'prenhez ectopica', 'gravidez ectopica', 'metotrexato ectopica', 'salpingostomia', 'salpingectomia',
        'mola hidatiforme', 'doenca trofoblastica gestacional', 'dtg', 'vilosidades corionicas'
    ]) or match_any(topic_norm, ['abortamento', 'gravidez ectopica', 'mola hidatiforme', 'hemorragias da 1 metade', 'hemorragias da primeira metade']):
        return "Hemorragias da Primeira Metade: Abortamento, Ectópica e Mola", 1.0, "Hemorragias da 1ª metade da gestação (Abortamento, Ectópica, Mola)."

    # 2. Hemorragias da Segunda Metade: Placenta Prévia e DPP
    if match_any(full_norm, [
        'descolamento prematuro de placenta', 'dpp', 'utero de couvelaire', 'placenta previa', 'placenta de insercao baixa',
        'acretismo placentario', 'placenta acreta', 'placenta increta', 'placenta percreta', 'rotura uterina',
        'rotura de vasa previa', 'sinal de bandl-frommel', 'sinal de bandl'
    ]) or match_any(topic_norm, ['dpp', 'placenta previa', 'acretismo', 'hemorragias da 2 metade', 'hemorragias da segunda metade']):
        return "Hemorragias da Segunda Metade: Placenta Prévia e DPP", 1.0, "Hemorragias da 2ª metade da gestação (DPP, Placenta Prévia, Acretismo, Roturas)."

    # 3. Síndromes Hipertensivas na Gravidez (Pré-eclâmpsia e Eclâmpsia)
    if match_any(full_norm, [
        'pre-eclampsia', 'eclampsia', 'sindrome hellp', 'sulfato de magnesio', 'esquema de zuspan', 'esquema de sibai',
        'gluconato de calcio', 'hipertensao gestacional', 'hipertensao arterial cronica na gestacao', 'hac na gestacao',
        'proteinuria na gestacao', 'anti-hipertensivo na gravidez', 'hidralazina venosa', 'metildopa'
    ]) or match_any(topic_norm, ['pre-eclampsia', 'eclampsia', 'sindrome hellp', 'hipertensao na gestacao', 'sindromes hipertensivas']):
        return "Síndromes Hipertensivas na Gravidez (Pré-eclâmpsia e Eclâmpsia)", 1.0, "Distúrbios hipertensivos na gestação (Pré-eclâmpsia, Eclâmpsia, Síndrome HELLP)."

    # 4. Diabetes Gestacional e Pré-Gestacional
    if match_any(full_norm, [
        'diabetes gestacional', 'dmg', 'teste oral de tolerancia a glicose na gestacao', 'totg 75g', 'glicemia de jejum no pre-natal',
        'insulina na gestacao', 'macrossomia fetal por diabetes'
    ]) or match_any(topic_norm, ['diabetes gestacional', 'dmg', 'diabetes e gravidez']):
        return "Diabetes Gestacional e Pré-Gestacional", 1.0, "Rastreamento e manejo do diabetes mellitus gestacional e pré-gestacional."

    # 5. Infecções Perinatais e Transmissão Vertical
    if match_any(full_norm, [
        'transmissao vertical do hiv', 'tarv no pre-natal', 'zidovudina no parto', 'sifilis na gestacao',
        'penicilina benzatina na gestante', 'vdrl na gestacao', 'estreptococo do grupo b', 'egb', 'streptococcus agalactiae',
        'swab vaginal e retal egb', 'profilaxia intraparto para egb', 'toxoplasmose gestacional', 'espiramicina',
        'sulfadiazina e pirimetamina na gestante', 'hepatite b na gestacao'
    ]) or match_any(topic_norm, ['transmissao vertical', 'sifilis gestacional', 'hiv e gestacao', 'estreptococo do grupo b', 'egb']):
        return "Infecções Perinatais e Transmissão Vertical (HIV, Sífilis, Hepatites, EGB)", 1.0, "Prevenção da transmissão vertical e infecções perinatais (HIV, Sífilis, EGB, Toxoplasmose)."

    # 6. Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade
    if match_any(full_norm, [
        'restricao de crescimento intrauterino', 'rciu', 'dopplerfluxometria obstetrica', 'arteria umbilical fetal',
        'arteria cerebral media fetal', 'ducto venoso fetal', 'isoimunizacao rh', 'imunoglobulina anti-d',
        'coombs indireto na gestante', 'gestacao gemelar', 'gemelaridade', 'monocorial', 'diamniotica', 'sindrome de transfusao feto-fetal', 'stff'
    ]) or match_any(topic_norm, ['rciu', 'doppler fetal', 'isoimunizacao rh', 'gemelaridade', 'medicina fetal']):
        return "Medicina Fetal: RCIU, Isoimunização Rh e Gemelaridade", 1.0, "Propedêutica fetal avançada (Doppler, RCIU, Isoimunização Rh, Gemelaridade)."

    # 7. Avaliação da Vitalidade Fetal, Cardiotocografia e Sofrimento Fetal
    if match_any(full_norm, [
        'cardiotocografia', 'ctg', 'perfil biofisico fetal', 'pbf', 'desaceleracao precoce', 'dip 1', 'dip i',
        'desaceleracao tardia', 'dip 2', 'dip ii', 'desaceleracao variavel', 'dip 3', 'dip iii', 'variabilidade da fcf',
        'sofrimento fetal agudo', 'liquido meconial intraparto', 'microanalise de sangue de couro cabeludo fetal'
    ]) or match_any(topic_norm, ['vitalidade fetal', 'cardiotocografia', 'sofrimento fetal', 'pbf']):
        return "Avaliação da Vitalidade Fetal, Cardiotocografia e Sofrimento Fetal", 1.0, "Monitorização da vitalidade fetal anteparto e intraparto (Cardiotocografia, PBF)."

    # 8. Amniorrexe Prematura (RPMO) e Corioamnionite
    if match_any(full_norm, [
        'amniorrexe prematura', 'rpmo', 'rotura prematura de membranas ovulares', 'corioamnionite', 'teste da cristalizacao do muco',
        'teste de nitrazina', 'amnisure', 'latencia da rpmo'
    ]) or match_any(topic_norm, ['amniorrexe', 'rpmo', 'corioamnionite']):
        return "Amniorrexe Prematura (RPMO) e Corioamnionite", 1.0, "Rotura prematura de membranas ovulares (RPMO) e infecção intra-amniótica."

    # 9. Trabalho de Parto Prematuro e Tocólise
    if match_any(full_norm, [
        'trabalho de parto prematuro', 'tpp', 'tocolise', 'nifedipino tocolise', 'atosibana', 'corticoide antenatal',
        'betametasona para maturidade pulmonar', 'neuroprotecao com sulfato de magnesio', 'comprimento do colo uterino por usg'
    ]) or match_any(topic_norm, ['parto prematuro', 'tpp', 'tocolise', 'maturidade pulmonar fetal']):
        return "Trabalho de Parto Prematuro e Tocólise", 1.0, "Diagnóstico e condução do trabalho de parto prematuro, tocólise e corticoterapia."

    # 10. Bacia Obstétrica, Estática Fetal e Mecanismo do Parto
    if match_any(full_norm, [
        'estatica fetal', 'situacao fetal', 'apresentacao fetal', 'posicao fetal', 'variedade de posicao',
        'mecanismo do parto', 'insinuacao', 'descida', 'flexao', 'rotacao interna da cabeca', 'desprendimento',
        'planos de de lee', 'planos de hodge', 'bacia ginecoide', 'bacia androide', 'bacia antropoide', 'bacia platipeloide'
    ]) or match_any(topic_norm, ['mecanismo do parto', 'estatica fetal', 'planos de de lee', 'bacia obstetrica']):
        return "Bacia Obstétrica, Estática Fetal e Mecanismo do Parto", 1.0, "Estática fetal, pelvimetria e tempos do mecanismo de parto."

    # 11. Assistência Clínica ao Trabalho de Parto, Partograma e Distocias
    if match_any(full_norm, [
        'partograma', 'fase ativa do trabalho de parto', 'periodo expulsivo', 'dequitamento', 'periodo de gmt',
        'parto taquitocico', 'fase ativa prolongada', 'parada secundaria da dilatacao', 'parada secundaria da descida',
        'periodo pelvico prolongado', 'distocia de ombro', 'manobra de mcroberts', 'inducao do parto', 'indice de bishop',
        'misoprostol inducao', 'ocitocina', 'episiotomia', 'forceps', 'vacuo-extrator', 'cesariana indicacoes'
    ]) or match_any(topic_norm, ['trabalho de parto', 'partograma', 'distocias', 'inducao do parto', 'forceps', 'cesarea']):
        return "Assistência Clínica ao Trabalho de Parto, Partograma e Distocias", 1.0, "Condução do trabalho de parto normal, partograma, distocias e via de parto."

    # 12. Puerpério Fisiológico, Patológico e Hemorragia Pós-Parto
    if match_any(full_norm, [
        'hemorragia pos-parto', 'hpp', 'atonia uterina', 'massagem uterina', 'balao de bakri', 'sutura de b-lynch',
        'acido tranexamico hpp', '4 ts da hpp', 'infeccao puerperal', 'endometrite puerperal', 'clindamicina e gentamicina',
        'loquios', 'involucao uterina'
    ]) or match_any(topic_norm, ['puerperio', 'hemorragia pos-parto', 'hpp', 'atonia uterina', 'infeccao puerperal']):
        return "Puerpério Fisiológico, Patológico e Hemorragia Pós-Parto", 1.0, "Puerpério fisiológico/patológico e manejo da hemorragia pós-parto."

    # 13. Assistência Pré-Natal de Baixo e Alto Risco
    if match_any(full_norm, [
        'assistencia pre-natal', 'consultas de pre-natal', 'exames de rotina no pre-natal', 'calculo da dpp',
        'calculo da idade gestacional', 'regra de nagele', 'suplementacao de acido folico', 'ganho de peso gestacional',
        'altura uterina na gestacao'
    ]) or match_any(topic_norm, ['pre-natal', 'nagele', 'rotina de pre-natal']):
        return "Assistência Pré-Natal de Baixo e Alto Risco", 1.0, "Rotina, propedêutica e condutas na assistência pré-natal de baixo e alto risco."

    # 14. Condições Clínicas Intercorrentes na Gravidez
    if match_any(full_norm, [
        'trombofiliana na gestacao', 'saf na gestacao', 'apendicite na gestacao', 'colecistite na gestacao',
        'anemia na gestacao', 'asma na gestacao', 'tireoidopatia na gestacao', 'infeccao do trato urinario na gestante', 'bacteriuria assintomatica na gestante'
    ]) or match_any(topic_norm, ['intercorrencias clinicas na gravidez', 'itu na gestante', 'comorbidades na gravidez']):
        return "Condições Clínicas Intercorrentes na Gravidez", 1.0, "Patologias clínicas e cirúrgicas intercorrentes no ciclo gravídico."

    # 15. Causas de Mortalidade Materna e Estratégias de Redução
    if match_any(full_norm, [
        'morte materna direta', 'morte materna indireta', 'razao de mortalidade materna obstetrica',
        'principais causas de morte materna', 'quase-morte materna', 'near miss materno'
    ]) or match_any(topic_norm, ['mortalidade materna']):
        return "Causas de Mortalidade Materna e Estratégias de Redução", 1.0, "Causas diretas/indiretas de mortalidade materna e comitês de prevenção."

    # 16. Câncer de Mama: Rastreamento, Diagnóstico e Estadiamento
    if match_any(full_norm, [
        'cancer de mama', 'carcinoma ductal', 'birads', 'bi-rads', 'mamografia de rastreamento',
        'core biopsy de mama', 'linfonodo sentinela na mama', 'receptores hormonais her2', 'quadrantectomia', 'mastectomia'
    ]) or match_any(topic_norm, ['cancer de mama', 'birads', 'mamografia']):
        return "Câncer de Mama: Rastreamento, Diagnóstico e Estadiamento", 1.0, "Rastreamento mamográfico (BI-RADS), diagnóstico e conduta no câncer de mama."

    # 17. Mastologia Benigna: Fibroadenomas, Cistos e Mastites
    if match_any(full_norm, [
        'fibroadenoma de mama', 'cisto mamario', 'mastite puerperal', 'abscesso mamario', 'fluxo papilar',
        'derrame papilar serossanguinolento', 'papiloma intraductal', 'mastalgia ciclica', 'alteracao funcional benigna da mama'
    ]) or match_any(topic_norm, ['mastologia benigna', 'fibroadenoma', 'mastite', 'derrame papilar']):
        return "Mastologia Benigna: Fibroadenomas, Cistos e Mastites", 1.0, "Afecções mamárias benignas (Fibroadenoma, cistos, mastites e derrames papilares)."

    # 18. Câncer de Colo Uterino e Lesões Precursoras
    if match_any(full_norm, [
        'cancer de colo uterino', 'carcinoma epidermoide de colo', 'estadiamento figo cancer de colo',
        'histerectomia de wertheim-meigs', 'braquiterapia colo uterino'
    ]) or match_any(topic_norm, ['cancer de colo uterino', 'estadiamento cancer de colo']):
        return "Câncer de Colo Uterino e Lesões Precursoras", 1.0, "Câncer invasor de colo uterino, estadiamento FIGO e condutas terapêuticas."

    # 19. Rastreamento Citopatológico e Conduta em Lesões Cervicais (HPV)
    if match_any(full_norm, [
        'papanicolaou', 'preventivo de colo', 'lesao intraepitelial de alto grau', 'hsil', 'lsil', 'asc-us', 'asc-h',
        'colposcopia', 'zona de transformacao', 'aceto-branco', 'schiller positivo', 'nic 1', 'nic 2', 'nic 3',
        'conizacao de colo', 'caf', 'vacina hpv na mulher'
    ]) or match_any(topic_norm, ['papanicolaou', 'hpv', 'colposcopia', 'lesoes precursoras de colo', 'hsil', 'lsil', 'asc-us']):
        return "Rastreamento Citopatológico e Conduta em Lesões Cervicais (HPV)", 1.0, "Rastreamento citopatológico (Bethesda), colposcopia e manejo de lesões pré-neoplásicas do colo."

    # 20. Afecções do Corpo Uterino, Endométrio e Sangramento Pós-Menopausa
    if match_any(full_norm, [
        'cancer de endometrio', 'hiperplasia endometrial', 'hiperplasia com atipias', 'sangramento pos-menopausa',
        'espessamento endometrial na usg', 'polipo endometrial', 'biopsia de endometrio', 'aspirador de pipelle'
    ]) or match_any(topic_norm, ['cancer de endometrio', 'hiperplasia endometrial', 'sangramento pos-menopausa']):
        return "Afecções do Corpo Uterino, Endométrio e Sangramento Pós-Menopausa", 1.0, "Propedêutica do sangramento pós-menopausa e neoplasias endometriais."

    # 21. Sangramento Uterino Anormal (SUA) e Classificação PALM-COEIN / Miomatose
    if match_any(full_norm, [
        'sangramento uterino anormal', 'sua', 'palm-coein', 'leiomioma uterino', 'mioma submucoso', 'mioma intramural',
        'mioma subseroso', 'miomatose uterina', 'miomectomia', 'histerectomia por mioma', 'acido tranexamico no sua',
        'diu de levonorgestrel no sua'
    ]) or match_any(topic_norm, ['sangramento uterino anormal', 'sua', 'miomatose', 'mioma', 'palm-coein']):
        return "Sangramento Uterino Anormal (SUA) e Classificação PALM-COEIN / Miomatose", 1.0, "Classificação PALM-COEIN, diagnóstico e tratamento de miomatose e SUA."

    # 22. Endometriose, Adenomiose e Dor Pélvica Crônica
    if match_any(full_norm, [
        'endometriose', 'endometrioma ovariano', 'adenomiose', 'dor pelvica cronica', 'dismenorreia secundaria',
        'dispareunia de profundidade', 'implantes endometrioticos', 'videolaparoscopia endometriose'
    ]) or match_any(topic_norm, ['endometriose', 'adenomiose', 'dor pelvica cronica']):
        return "Endometriose, Adenomiose e Dor Pélvica Crônica", 1.0, "Quadro clínico, mapeamento por imagem e manejo de endometriose e adenomiose."

    # 23. Massas Anexiais e Neoplasias Ovarianas
    if match_any(full_norm, [
        'massa anexial', 'cisto de ovario', 'cancer de ovario', 'ca-125', 'teratoma maduro', 'cisto dermoide',
        'cistoadenoma', 'escore iota', 'tumor de celulas da granulosa'
    ]) or match_any(topic_norm, ['massa anexial', 'cisto ovariano', 'cancer de ovario', 'iota']):
        return "Massas Anexiais e Neoplasias Ovarianas", 1.0, "Diagnóstico diferencial e conduta nas massas anexiais e neoplasias de ovário."

    # 24. Métodos Contraceptivos: Hormonais, DIU e Cirúrgicos
    if match_any(full_norm, [
        'contracepcao', 'anticoncepcional hormonal combinado', 'anticoncepcional de progestagenio', 'diu de cobre',
        'diu hormonal', 'diu de levonorgestrel', 'mirena', 'implante subdermico', 'criterios de elegibilidade da oms',
        'laqueadura tubaria', 'anticoncepcao de emergencia', 'pilula do dia seguinte'
    ]) or match_any(topic_norm, ['contracepcao', 'metodos contraceptivos', 'diu', 'anticoncepcional']):
        return "Métodos Contraceptivos: Hormonais, DIU e Cirúrgicos", 1.0, "Critérios de elegibilidade médica da OMS e métodos contraceptivos."

    # 25. Climatério, Menopausa e Terapia de Reposição Hormonal (TRH)
    if match_any(full_norm, [
        'climaterio', 'menopausa', 'terapia de reposicao hormonal', 'trh', 'fogachos', 'sintomas vasomotores da menopausa',
        'janela de oportunidade da trh', 'contraindicacoes da trh', 'atrofia urogenital pos-menopausa', 'estrogenioterapia'
    ]) or match_any(topic_norm, ['climaterio', 'menopausa', 'trh', 'terapia hormonal']):
        return "Climatério, Menopausa e Terapia de Reposição Hormonal (TRH)", 1.0, "Manejo da transição menopáusica e indicações/contraindicações da TRH."

    # 26. Investigação das Amenorreias e Síndrome dos Ovários Policísticos (SOP)
    if match_any(full_norm, [
        'amenorreia primaria', 'amenorreia secundaria', 'sindrome dos ovarios policisticos', 'sop', 'criterios de rotterdam',
        'hirsutismo', 'escala de ferriman-gallwey', 'teste da progesterona', 'teste do estrogenio e progesterona',
        'sindrome de asherman', 'falencia ovariana prematura'
    ]) or match_any(topic_norm, ['amenorreia', 'sop', 'ovarios policisticos', 'hirsutismo']):
        return "Investigação das Amenorreias e Síndrome dos Ovários Policísticos (SOP)", 1.0, "Fluxograma diagnóstico de amenorreias e manejo clínico da SOP."

    # 27. Fisiologia do Ciclo Menstrual e Eixo Hipotálamo-Hipófise-Ovário
    if match_any(full_norm, [
        'fisiologia do ciclo menstrual', 'fase folicular', 'fase lutea', 'pico de lh', 'ovulacao', 'gnrh',
        'estradiol', 'progesterona no ciclo', 'corpo luteo'
    ]) or match_any(topic_norm, ['ciclo menstrual', 'fisiologia menstrual', 'eixo hho']):
        return "Fisiologia do Ciclo Menstrual e Eixo Hipotálamo-Hipófise-Ovário", 1.0, "Endocrinologia ginecológica e fisiologia do ciclo ovulatório."

    # 28. Investigação e Propêdêutica da Infertilidade Conjugal
    if match_any(full_norm, [
        'infertilidade conjugal', 'investigacao de infertilidade', 'espermograma', 'histerossalpingografia',
        'fator tuboperitoneal', 'reserva ovariana', 'hormonio antimulleriano', 'fiv', 'reproducao assistida'
    ]) or match_any(topic_norm, ['infertilidade', 'reproducao assistida', 'espermograma']):
        return "Investigação e Propêdêutica da Infertilidade Conjugal", 1.0, "Propedêutica mínima do casal infértil e técnicas de reprodução assistida."

    # 29. Vulvovaginites e Diagnóstico Diferencial dos Corrimentos Vaginais
    if match_any(full_norm, [
        'vulvovaginite', 'candidíase vulvovaginal', 'vaginose bacteriana', 'gardnerella vaginalis', 'criterios de amsel',
        'clue cells', 'teste das aminas positivo', 'trichomonas vaginalis', 'tricomoniase', 'vaginite descamativa inflamatória'
    ]) or match_any(topic_norm, ['vulvovaginite', 'candidíase', 'vaginose', 'tricomoniase', 'corrimento vaginal']):
        return "Vulvovaginites e Diagnóstico Diferencial dos Corrimentos Vaginais", 1.0, "Diagnóstico clínico/microscópico e tratamento dos corrimentos vaginais."

    # 30. Doença Inflamatória Pélvica (DIP) e Atendimento à Violência Sexual
    if match_any(full_norm, [
        'doenca inflamatoria pelvica', 'dip', 'criterios de monif', 'abscesso tubo-ovariano', 'violencia sexual contra mulher',
        'profilaxia pos-exposicao violencia sexual', 'anticoncepcao de emergencia violencia'
    ]) or match_any(topic_norm, ['dip', 'doenca inflamatoria pelvica', 'violencia sexual']):
        return "Doença Inflamatória Pélvica (DIP) e Atendimento à Violência Sexual", 1.0, "DIP (critérios diagnósticos, estadiamento de Monif) e protocolo pós-violência sexual."

    # 31. Úlceras Genitais e Infecções Sexualmente Transmissíveis na Mulher
    if match_any(full_norm, [
        'ulcera genital', 'cancro duro', 'cancro mole', 'haemophilus ducreyi', 'herpes genital', 'donovanose',
        'linfogranuloma venereo', 'treponema pallidum'
    ]) or match_any(topic_norm, ['ulceras genitais', 'cancro', 'ist feminina']):
        return "Úlceras Genitais e Infecções Sexualmente Transmissíveis na Mulher", 1.0, "Diagnóstico sindrômico e etiológico de úlceras genitais femininas."

    # 32. Uroginecologia: Incontinência Urinária e Prolapso Genital
    if match_any(full_norm, [
        'incontinencia urinaria de esforco', 'iue', 'bexiga hiperativa', 'incontinencia de urgencia', 'estudo urodinamico',
        'sling suburetral', 'treinamento dos musculos do assoalho pelvico', 'prolapso de orgaos pelvicos', 'pop-q',
        'cistocele', 'retocele', 'prolapso uterino', 'pessario vaginal'
    ]) or match_any(topic_norm, ['incontinencia urinaria', 'uroginecologia', 'pop-q', 'prolapso genital']):
        return "Uroginecologia: Incontinência Urinária e Prolapso Genital", 1.0, "Incontinência urinária feminina e estadiamento de prolapsos genitais (POP-Q)."

    # 33. Patologias Benignas e Neoplásicas da Vulva e Vagina
    if match_any(full_norm, [
        'liquen escleroso vulvar', 'cancer de vulva', 'neoplasia intraepitelial vulvar', 'vin', 'bartolinite', 'cisto de bartholin'
    ]) or match_any(topic_norm, ['vulva', 'liquen escleroso', 'patologia vulvar']):
        return "Patologias Benignas e Neoplásicas da Vulva e Vagina", 1.0, "Patologias benignas, dermatoses e neoplasias vulvovaginais."

    # 34. Fundamentos em Sexualidade Humana e Saúde Reprodutiva
    if match_any(full_norm, [
        'sexualidade humana', 'saude reprodutiva', 'direitos sexuais e reprodutivos', 'planejamento familiar'
    ]) or match_any(topic_norm, ['sexualidade', 'saude reprodutiva']):
        return "Fundamentos em Sexualidade Humana e Saúde Reprodutiva", 1.0, "Sexualidade humana e diretrizes de saúde reprodutiva."

    # 35. Disfunções Sexuais Femininas e Dispareunia
    if match_any(full_norm, [
        'disfuncao sexual feminina', 'dispareunia', 'vaginismo', 'transtorno do interesse/excitacao sexual feminino', 'dor genitopelvica'
    ]) or match_any(topic_norm, ['dispareunia', 'vaginismo', 'disfuncao sexual']):
        return "Disfunções Sexuais Femininas e Dispareunia", 1.0, "Disfunções sexuais femininas e dor na relação sexual."

    # 36. Fístulas Urogenitais e Retovaginais
    if match_any(full_norm, [
        'fistula vesicovaginal', 'fistula retovaginal', 'fistula urogenital', 'perda involuntaria de urina continua pos-cirurgia pelvica'
    ]) or match_any(topic_norm, ['fistula vesicovaginal', 'fistula retovaginal', 'fistulas']):
        return "Fístulas Urogenitais e Retovaginais", 1.0, "Fístulas vesicovaginais e retovaginais pós-parto ou pós-cirúrgicas."

    # 37. Anatomia Cirúrgica e Estruturas Pélvicas Femininas
    if match_any(full_norm, [
        'anatomia pelvica feminina', 'ligamento redondo', 'ligamento cardeal', 'ligamento macenrodt', 'ligamento uterossacro',
        'arteria uterina relacao com ureter', 'fossa ovárica', 'espaço retroperitoneal pelvico'
    ]) or match_any(topic_norm, ['anatomia pelvica', 'anatomia cirurgica go']):
        return "Anatomia Cirúrgica e Estruturas Pélvicas Femininas", 1.0, "Anatomia vascular e ligamentar da pelve feminina."

    # Default fallback to Parto if obstétrico or SUA if ginecológico
    if match_any(full_norm, ['parto', 'gestante', 'semanas de gestacao', 'feto', 'obstetrico']):
        return "Assistência Clínica ao Trabalho de Parto, Partograma e Distocias", 0.90, "Manejo obstétrico geral e trabalho de parto."

    return "Sangramento Uterino Anormal (SUA) e Classificação PALM-COEIN / Miomatose", 0.90, "Ginecologia geral e afecções uterinas."

def process_block3(apply=False):
    conn = sqlite3.connect("app/backend/medquest.db")
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT q.id, q.stem, q.topic, q.subtema_orig, q.area, q.subtema, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.area = 'Ginecologia e Obstetrícia'
        ORDER BY q.id
    """).fetchall()
    
    print(f"==================================================")
    print(f"PROCESSANDO BLOCO 3: GINECOLOGIA E OBSTETRÍCIA ({len(rows)} QUESTÕES)")
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
        
        new_sub, conf, rationale = classify_go(q_dict)
        distribution[new_sub] = distribution.get(new_sub, 0) + 1
        
        if old_sub != new_sub:
            changes.append({
                "id": qid,
                "old_subtema": old_sub,
                "new_subtema": new_sub,
                "confidence": conf,
                "rationale": rationale
            })
            
    print(f"\nTotal de reclassificações no Bloco 3: {len(changes)} ({len(changes)/len(rows)*100:.1f}%)")
    print(f"\n--- DISTRIBUIÇÃO DOS 37 SUBTEMAS DO BLOCO 3 ---")
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
        print(f"\n✅ {len(changes)} questões do Bloco 3 atualizadas no banco com sucesso!")
        
    return changes

if __name__ == "__main__":
    apply_flag = "--apply" in sys.argv
    process_block3(apply=apply_flag)
