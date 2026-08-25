"""
Classificador de Alta Precisão - Bloco 4: Cirurgia (48 Subtemas Canônicos)
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

def classify_cirurgia(q):
    stem = q.get('stem', '')
    alts = q.get('alternatives', '')
    exp = q.get('explanation', '')
    topic = q.get('topic', '')
    subtema_orig = q.get('subtema_orig', '')
    
    stem_norm = norm(stem)
    topic_norm = norm(topic)
    sub_orig_norm = norm(subtema_orig)
    full_norm = norm(f"{stem} {topic} {subtema_orig}")    # 1. Particularidades das Queimaduras na Faixa Etária Pediátrica
    if match_any(full_norm, ['queimadura', 'queimado', 'escaldadura', 'scq']) and match_any(stem_norm, [
        'lactente', 'meses de vida', 'recem-nascido', 'crianca de 1 ano', 'crianca de 2 ano', 'crianca de 3 ano',
        'crianca de 4 ano', 'menino de 2 ano', 'menina de 2 ano', 'regra dos nove infantil', 'lund e browder'
    ]):
        return "Particularidades das Queimaduras na Faixa Etária Pediátrica", 1.0, "Queimaduras pediátricas, cálculo de superfície corporal queimada (Lund-Browder) e reposição volêmica."

    # 2. Atendimento ao Paciente Queimado e Reposição Volêmica (Adulto / Geral)
    if match_any(full_norm, [
        'queimadura', 'paciente queimado', 'grande queimado', 'formula de parkland', 'formula de brooke',
        'escarotomia', 'flictena', 'queimadura de 2o grau', 'queimadura de 3o grau', 'intoxicacao por monoxido de carbono',
        'queimadura de via aerea', 'queimadura eletrica'
    ]) or match_any(topic_norm, ['queimado', 'queimados', 'atendimento inicial aos queimados']):
        if not match_any(full_norm, ['marjolin', 'cicatriz antiga de queimadura']):
            return "Atendimento ao Paciente Queimado e Reposição Volêmica", 1.0, "Atendimento ao paciente queimado adulto, estratificação de gravidade e reposição volêmica."

    # 3. Cicatrização, Tratamento de Feridas, Enxertos e Retalhos
    if match_any(full_norm, [
        'gangrena de fournier', 'fournier', 'fasceite necrosante', 'fasceite necrotizante', 'infeccao necrosante de partes moles',
        'morel-lavallee', 'ferimento descolante', 'degloving', 'lesao por pressao', 'curativo por pressao negativa',
        'enxerto de pele', 'enxertia cutanea', 'retalho miocutaneo', 'retalho microcirurgico', 'queloidede',
        'cicatriz hipertrofica', 'fases da cicatrizacao', 'fatores de crescimento cicatrizacao'
    ]) or match_any(topic_norm, ['cicatrizacao', 'enxertos', 'retalhos', 'feridas', 'fournier', 'curativos']):
        return "Cicatrização, Tratamento de Feridas, Enxertos e Retalhos", 1.0, "Fisiologia da cicatrização, infecções necrosantes, desbridamento, enxertos e retalhos."

    # 4. Oncologia Cutânea: Melanoma, CBC e CEC
    if match_any(full_norm, [
        'melanoma cutaneo', 'melanoma nodular', 'melanoma extensivo superficial', 'indice de breslow', 'nivel de clark',
        'linfonodo sentinela no melanoma', 'carcinoma basocelular', 'cbc cutaneo', 'carcinoma espinocelular cutaneo',
        'cec cutaneo', 'ulcera de marjolin', 'ceratoacantoma'
    ]) or match_any(topic_norm, ['melanoma', 'cbc', 'cec cutaneo', 'oncologia cutanea', 'tumores de pele']):
        return "Oncologia Cutânea: Melanoma, CBC e CEC", 1.0, "Neoplasias malignas da pele (Melanoma, Carcinoma Basocelular e Carcinoma Espinocelular)."

    # 5. Polipose Adenomatosa Familiar (PAF) e Síndromes Hereditárias
    if match_any(full_norm, [
        'polipose adenomatosa familiar', 'paf', 'gene apc', 'sindrome de lynch', 'hnpcc', 'sindrome de peutz-jeghers',
        'sindrome de gardner', 'sindrome de turcot', 'sindrome de cowden', 'polipos adenomatosos intestinais multiplos'
    ]) or match_any(topic_norm, ['paf', 'polipose', 'lynch', 'sindromes hereditarias']):
        return "Polipose Adenomatosa Familiar (PAF) e Síndromes Hereditárias", 1.0, "Síndromes hereditárias de polipose intestinal e predisposição ao câncer colorretal."

    # 6. Câncer de Pulmão, Nódulo Pulmonar Solitário e Tumores do Mediastino
    if match_any(full_norm, [
        'nodulo pulmonar solitario', 'nps', 'cancer de pulmao', 'carcinoma epidermoide de pulmao', 'adenocarcinoma de pulmao',
        'carcinoma de pequenas celulas', 'timoma', 'tumor de mediastino anterior', 'miastenia gravis cirurgica', 'teratoma de mediastino'
    ]) and not match_any(full_norm, ['trauma toracico', 'hemotorax macico', 'drenagem de torax no trauma']):
        return "Câncer de Pulmão, Nódulo Pulmonar Solitário e Tumores do Mediastino", 1.0, "Investigação do nódulo pulmonar solitário, estadiamento do câncer de pulmão e tumores mediastinais."

    # 7. Neoplasias do Trato Gastrointestinal
    if match_any(full_norm, [
        'cancer gastrico', 'adenocarcinoma gastrico', 'linfadenectomia d2', 'classificacao de bormann', 'classificacao de lauren',
        'cancer de colon', 'adenocarcinoma de colon', 'cancer de reto', 'ressecção anterior do reto', 'amputacao abdominoperineal do reto',
        'cirurgia de miles', 'cancer de esofago', 'esofagectomia', 'cancer de pancreas', 'adenocarcinoma ductal pancreatico',
        'duodenopancreatectomia', 'cirurgia de whipple', 'gist gastrico', 'tumor estromal gastrointestinal',
        'cancer colorretal', 'adenocarcinoma de estomago', 'tumores periampulares'
    ]) or match_any(topic_norm, ['cancer gastrico', 'cancer de colon', 'cancer de reto', 'cancer de pancreas', 'cancer de esofago', 'neoplasias gastrointestinais', 'cancer colorretal (cir)', 'adenocarcinoma de estomago', 'tumores periampulares']):
        return "Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)", 1.0, "Diagnóstico, estadiamento e terapêutica cirúrgica dos tumores do trato gastrointestinal."

    # 8. Abordagem Cirúrgica das Doenças Inflamatórias Intestinais
    if match_any(full_norm, [
        'doenca de crohn cirurgia', 'retocolite ulcerativa cirurgia', 'proctocolectomia total com bolsa ileal',
        'estrituroplastia', 'megacolon toxico cirurgia', 'fistula perianal complexa por crohn'
    ]) or match_any(topic_norm, ['doenca de crohn cirurgica', 'rcu cirurgica', 'dii cirurgia']):
        return "Abordagem Cirúrgica das Doenças Inflamatórias Intestinais (Crohn e RCU)", 1.0, "Indicações cirúrgicas e técnicas operatórias na Doença de Crohn e Retocolite Ulcerativa."

    # 9. Distúrbios Motores do Esôfago, Megaesôfago e Síndrome Disfágica
    if match_any(full_norm, [
        'acalasia', 'megaesofago chagasico', 'cardiomiotomia a heller', 'classificacao de rezende', 'dilatacao pneumatica do esofago',
        'diverticulo de zenker', 'miotomia do cricofaringeo', 'espasmo esofagiano difuso', 'sindrome disfagica'
    ]) or match_any(topic_norm, ['acalasia', 'megaesofago', 'diverticulo de zenker', 'disturbios motores do esofago', 'disfagia (cir)']):
        return "Distúrbios Motores do Esôfago, Megaesôfago e Síndrome Disfágica", 1.0, "Distúrbios motores esofágicos, megaesôfago e divertículos do esôfago."

    # 10. Doença do Refluxo Gastroesofágico (DRGE) e Úlcera Péptica
    if match_any(full_norm, [
        'drge cirurgica', 'refluxo gastroesofagico cirurgia', 'fundoplicatura de nissen', 'fundoplicatura laparoscopica',
        'esofago de barrett', 'hernia de hiato por deslizamento', 'hernia paraesofagica', 'phmetria esofagica', 'dispepsia e ibps'
    ]) or match_any(topic_norm, ['drge (cir)', 'drge e barret (cm)', 'refluxo']):
        if not match_any(full_norm, ['perfurativa', 'hemorragia digestiva alta', 'forrest']):
            return "Doença do Refluxo Gastroesofágico (DRGE) e Úlcera Péptica", 1.0, "Indicações de cirurgia antirrefluxo (Fundoplicatura) e vigilância do Esôfago de Barrett."

    # 11. Hemorragia Digestiva Alta e Baixa na Emergência Cirúrgica
    if match_any(full_norm, [
        'hemorragia digestiva alta', 'hda cirurgica', 'classificacao de forrest', 'endoscopia digestiva de urgencia',
        'varizes esofagicas sangramento', 'balao de sengstaken-blakemore', 'hemorragia digestiva baixa', 'hdb',
        'cintilografia com hemacias marcadas sangramento', 'angioembolizacao hda'
    ]) or match_any(topic_norm, ['hda', 'hdb', 'hemorragia digestiva', 'sangramento digestivo']):
        return "Hemorragia Digestiva Alta e Baixa na Emergência Cirúrgica", 1.0, "Abordagem da hemorragia digestiva alta e baixa na emergência cirúrgica."

    # 12. Cirurgia Bariátrica e Metabólica
    if match_any(full_norm, [
        'cirurgia bariatrica', 'bypass gastrico em y de roux', 'gastrectomia vertical', 'sleeve gastrico',
        'fistula da anastomose gastrojejunal', 'hernia interna pos-bariatrica', 'espaco de petersen', 'estenose da anastomose bariatrica'
    ]) or match_any(topic_norm, ['cirurgia bariatrica', 'bariatrica', 'obesidade cirurgia']):
        return "Cirurgia Bariátrica e Metabólica", 1.0, "Técnicas cirúrgicas bariátricas e manejo de complicações pós-operatórias precoces/tardias."

    # 13. Cirurgia Pediátrica e Malformações Digestivas Neonatais
    if match_any(full_norm, [
        'estenose hipertrofica do piloro', 'atresia de esofago', 'fistula traqueoesofagica', 'hernia diafragmatica congenita',
        'bochdalek', 'morgagni', 'atresia duodenal', 'sinal da dupla bolha', 'ma rotacao intestinal', 'volvo de intestino medio',
        'doenca de hirschsprung', 'anomalia anorretal', 'imperfuracao anal', 'onfalocele', 'gastrosquise', 'atresia biliar', 'cirurgia de kasai',
        'intussuscepcao intestinal'
    ]) or match_any(topic_norm, ['cirurgia pediatrica', 'atresia de esofago', 'estenose hipertrofica do piloro', 'hernia diafragmatica', 'intussuscepcao intestinal (cipe)']):
        return "Cirurgia Pediátrica e Malformações Digestivas Neonatais", 1.0, "Malformações digestivas congênitas e emergências cirúrgicas neonatais e pediátricas."

    # 14. Cirurgia de Cabeça e Pescoço: Afecções Cervicais Benignas e Cistos Congênitos
    if match_any(full_norm, [
        'cisto tireoglosso', 'procedimento de sistrunk', 'cisto branquial', 'higroma cistico', 'adenoma pleomorfico de parotida',
        'tumor de warthin', 'parotidectomia', 'glandula submandibular litiase', 'triangulos cervicais', 'linfonodo cervical biopsia lesao do nervo acessorio'
    ]) and not match_any(full_norm, ['carcinoma papilifero', 'carcinoma medular', 'cancer de laringe']):
        return "Cirurgia de Cabeça e Pescoço: Afecções Cervicais Benignas e Cistos Congênitos", 1.0, "Cistos congênitos cervicais, afecções salivares benignas e anatomia cervical cirúrgica."

    # 15. Neoplasias de Cabeça e Pescoço e Nódulos Tireoidianos Cirúrgicos
    if match_any(full_norm, [
        'nodulo tireoidiano', 'classificacao de bethesda', 'carcinoma papilifero de tireoide', 'carcinoma folicular de tireoide',
        'carcinoma medular de tireoide', 'tireoidectomia total', 'lesao do nervo laringeo recorrente', 'hipoparatireoidismo pos-tireoidectomia',
        'cancer de laringe', 'cancer de cavidade oral', 'cancer de lingua', 'esvaziamento cervical radical'
    ]) or match_any(topic_norm, ['nodulo tireoidiano', 'cancer de tireoide', 'cancer de cabeca e pescoco', 'tireoidectomia']):
        return "Neoplasias de Cabeça e Pescoço e Nódulos Tireoidianos Cirúrgicos", 1.0, "Nódulos tireoidianos cirúrgicos, carcinomas de tireoide e CEC de cabeça e pescoço."

    # 16. Coloproctologia: Doenças Orificiais e Afecções Colorretais
    if match_any(full_norm, [
        'doenca hemorroidaria', 'hemorroida interna', 'hemorroida externa', 'trombose hemorroidaria', 'hemorroidectomia de ferguson',
        'hemorroidectomia de milligan-morgan', 'fissura anal', 'esfincterotomia lateral interna', 'abscesso perianal',
        'fistula anorretal', 'regra de goodsall-salmon', 'cisto pilonidal', 'prolapso retal', 'cancer de canal anal'
    ]) or match_any(topic_norm, ['hemorroida', 'fissura anal', 'abscesso perianal', 'fistula perianal', 'proctologia', 'doencas orificiais']):
        return "Coloproctologia: Doenças Orificiais e Afecções Colorretais", 1.0, "Doenças orificiais anorretais (Hemorroidas, Fissuras, Abscessos, Fístulas) e afecções proctológicas."

    # 17. Uro-Oncologia: Câncer de Próstata, Rim, Bexiga e Testículo
    if match_any(full_norm, [
        'cancer de prostata', 'escore de gleason', 'biopsia de prostata transretal', 'prostatectomia radical',
        'cancer de rim', 'carcinoma de celulas renais', 'angiomiolipoma renal', 'cancer de bexiga', 'rtu de bexiga',
        'cancer de testiculo', 'orquiectomia radical inguinal', 'torcao testicular', 'sinal de prehn', 'orquiepididimite'
    ]) or match_any(topic_norm, ['cancer de prostata', 'cancer renal', 'cancer de bexiga', 'cancer de testiculo', 'uro-oncologia']):
        return "Uro-Oncologia: Câncer de Próstata, Rim, Bexiga e Testículo", 1.0, "Neoplasias do trato geniturinário (Próstata, Rim, Bexiga, Testículo) e escroto agudo."

    # 18. Hiperplasia Prostática Benigna (HPB) e Litíase Urinária
    if match_any(full_norm, [
        'hiperplasia prostatica benigna', 'hpb', 'rtu de prostata', 'ipss', 'litiase urinaria', 'calculo ureteral',
        'colica nefritica', 'duplo j', 'nefrolitotripsia percutanea', 'ureterolitotripsia a laser', 'leco litotripsia'
    ]) or match_any(topic_norm, ['hpb', 'litiase urinaria', 'calculo renal cirurgia', 'urologia']):
        return "Hiperplasia Prostática Benigna (HPB) e Litíase Urinária", 1.0, "Tratamento clínico e cirúrgico da HPB e intervenções na litíase urinária."

    # 19. Aneurismas de Aorta Abdominal e Torácica
    if match_any(full_norm, [
        'aneurisma de aorta abdominal', 'aaa', 'disseccao de aorta', 'disseccao aortica', 'classificacao de stanford',
        'stanford a', 'stanford b', 'classificacao de debakey', 'correcao endovascular de aneurisma', 'evar', 'ruptura de aneurisma de aorta'
    ]) or match_any(topic_norm, ['aneurisma de aorta', 'disseccao de aorta', 'cirurgia vascular aorta']):
        return "Aneurismas de Aorta Abdominal e Torácica", 1.0, "Aneurismas de aorta e síndromes aórticas agudas (Dissecção aórtica, intervenção cirúrgica/EVAR)."

    # 20. Doença Arterial Obstrutiva Periférica e Oclusões Arteriais Agudas
    if match_any(full_norm, [
        'doenca arterial obstrutiva periferica', 'daop', 'claudicacao intermitente', 'isquemia critica de membro',
        'indice tornozelo-braco', 'itb', 'classificacao de fontaine', 'classificacao de rutherford', 'oclusao arterial aguda',
        'embolia arterial de membros', 'trombose arterial aguda', 'embolectomia com cateter de fogarty', 'revascularizacao periferica'
    ]) or match_any(topic_norm, ['daop', 'oclusao arterial aguda', 'isquemia de membro', 'cirurgia vascular periferica']):
        return "Doença Arterial Obstrutiva Periférica e Oclusões Arteriais Agudas", 1.0, "Quadro clínico e terapêutica da DAOP crônica e da oclusão arterial aguda de extremidades."

    # 21. Insuficiência Venosa Crônica e Trombose Venosa Profunda (TVP)
    if match_any(full_norm, [
        'trombose venosa profunda', 'tvp', 'tromboembolismo venoso cirurgico', 'tromboprofilaxia cirurgica', 'escore de caprini',
        'filtro de veia cava inferior', 'insuficiencia venosa cronica', 'classificacao ceap', 'varizes de membros inferiores', 'ulcera venosa maleolar',
        'sindromes compressivas (vasc)'
    ]) or match_any(topic_norm, ['tvp', 'trombose venosa', 'insuficiencia venosa', 'varizes', 'sindromes compressivas (vasc)']):
        return "Insuficiência Venosa Crônica e Trombose Venosa Profunda (TVP)", 1.0, "Profilaxia e manejo da TVP cirúrgica e insuficiência venosa crônica periférica."

    # 22. Cirurgia Cardíaca: Revascularização Miocárdica e Cirurgia Valvar
    if match_any(full_norm, [
        'revascularizacao miocardica cirurgia', 'ponte de safena cirurgia', 'enxerto de arteria toracica interna mamaria',
        'troca valvar mitral cirurgia', 'troca valvar aortica cirurgica', 'circulacao extracorporea', 'cec na cirurgia cardiaca'
    ]) or match_any(topic_norm, ['cirurgia cardiaca', 'revascularizacao miocardica', 'troca valvar']):
        return "Cirurgia Cardíaca: Revascularização Miocárdica e Cirurgia Valvar", 1.0, "Princípios da cirurgia de revascularização miocárdica e plastia/troca valvar."

    # 23. Cirurgia Torácica Geral e Doenças Pleurais
    if match_any(full_norm, [
        'empiema pleural cirurgia', 'decorticacao pleuropulmonar', 'derrame pleural parapneumonico complicado',
        'pneumotorax espontaneo primario', 'fuga aerea persistente', 'videotoracoscopia pleurodese', 'estenose traqueal pos-intubacao',
        'traqueostomia tecnica e indicacoes', 'cricotireoidostomia cirurgica', 'doencas traqueais', 'vias aereas (cir)'
    ]) or match_any(topic_norm, ['doencas traqueais', 'vias aereas (cir)', 'cirurgia toracica geral']):
        if not match_any(full_norm, ['trauma toracico', 'ferimento por arma de fogo no torax', 'toracostomia com drenagem no trauma']):
            return "Cirurgia Torácica Geral e Doenças Pleurais", 1.0, "Patologias pleurais benignas, pneumotórax espontâneo e cirurgia da via aérea traqueal."

    # 24. Fundamentos da Anestesiologia, Farmacologia e Bloqueios
    if match_any(full_norm, [
        'anestesiologia', 'anestesia geral', 'raquianestesia', 'anestesia peridural', 'bloqueador neuromuscular',
        'succinilcolina', 'rocuronio', 'sugamadex', 'hipertermia maligna', 'dantroleno', 'anestesico local',
        'bupivacaina', 'lidocaina sem vasoconstritor', 'toxicidade por anestesico local', 'emulsao lipidica intoxicacao'
    ]) or match_any(topic_norm, ['anestesiologia', 'anestesia', 'bloqueios', 'farmacologia anestesica']):
        return "Fundamentos da Anestesiologia, Farmacologia e Bloqueios", 1.0, "Farmacologia anestésica, toxicidade por anestésicos locais e técnicas de bloqueio regional."

    # 25. Trauma de Face e Pescoço (Trauma Cervical e Fraturas Maxilofaciais)
    if match_any(full_norm, [
        'trauma cervical', 'ferimento cervical penetrante', 'zonas do pescoco', 'zona i do pescoco', 'zona ii do pescoco',
        'zona iii do pescoco', 'lesao do platisma', 'fratura de mandíbula', 'fratura de le fort', 'le fort i', 'le fort ii',
        'le fort iii', 'fratura zigomatica', 'fratura blow-out da orbita', 'trauma maxilofacial'
    ]) or match_any(topic_norm, ['trauma de face', 'trauma cervical', 'fraturas maxilofaciais']):
        return "Trauma de Face e Pescoço (Trauma Cervical e Fraturas Maxilofaciais)", 1.0, "Trauma cervical contuso/penetrante e fraturas do esqueleto maxilofacial."

    # 26. Trauma Raquimedular (TRM) e Lesões Vertebrais
    if match_any(full_norm, [
        'trauma raquimedular', 'trm', 'choque neurogenico no trauma', 'choque medular', 'sindrome de brown-sequard',
        'sindrome medular anterior', 'sindrome medular central', 'fratura de chance', 'imobilizacao com colar cervical e prancha'
    ]) or match_any(topic_norm, ['trm', 'trauma raquimedular', 'coluna vertebral trauma']):
        return "Trauma Raquimedular (TRM) e Lesões Vertebrais", 1.0, "Abordagem do trauma raquimedular, síndromes medulares e estabilização da coluna."

    # 27. Trauma Ortopédico de Extremidades e Síndrome Compartimental
    if match_any(full_norm, [
        'sindrome compartimental de membro', 'pressao intracompartimental', 'fasciotomia descompressiva',
        'trauma vascular de extremidades', 'sinais duros de trauma vascular em membros', 'shunts vasculares no trauma'
    ]) or match_any(topic_norm, ['sindrome compartimental', 'trauma vascular de extremidades']):
        return "Trauma Ortopédico de Extremidades e Síndrome Compartimental", 1.0, "Lesões graves de extremidades, síndrome compartimental e trauma vascular associado."

    # 28. Fraturas Ósseas e Princípios Gerais de Osteossíntese
    if match_any(full_norm, [
        'fratura exposta', 'classificacao de gustilo-anderson', 'osteossintese com placa', 'haste intramedular',
        'fixador externo', 'consolidacao ossea por primeira intencao', 'pseudoartrose', 'fratura do colo do femur',
        'fratura de radio distal colles', 'fratura diafisaria de tibia', 'trauma osteomuscular'
    ]) or match_any(topic_norm, ['fraturas', 'fratura exposta', 'osteossintese', 'ortopedia geral', 'trauma osteomuscular', 'ortopedia']):
        return "Fraturas Ósseas e Princípios Gerais de Osteossíntese", 1.0, "Classificação, tratamento de urgência das fraturas expostas e princípios de osteossíntese."

    # 29. Ortopedia Pediátrica: Displasia do Quadril, Pé Torto e Epifisiólise
    if match_any(full_norm, [
        'displasia do desenvolvimento do quadril', 'ddq', 'manobra de ortolani', 'manobra de barlow', 'suspensório de pavlik',
        'pe torto congenito', 'metodo de ponseti', 'epifisiolise femoral proximal', 'doenca de legg-calve-perthes', 'sinovite transitoria do quadril'
    ]) or match_any(topic_norm, ['ortopedia pediatrica', 'displasia do quadril', 'epifisiolise', 'pe torto']):
        return "Ortopedia Pediátrica: Displasia do Quadril, Pé Torto e Epifisiólise", 1.0, "Patologias musculoesqueléticas da infância (DDQ, Pé Torto Congênito, Epifisiólise, Perthes)."

    # 30. Luxações Articulares e Lesões Ligamentares / Meniscais
    if match_any(full_norm, [
        'luxacao anterior do ombro', 'manobra de kocher luxacao', 'luxacao posterior do quadril', 'lesao do ligamento cruzado anterior',
        'lca', 'teste da gaveta anterior', 'teste de lachman', 'lesao meniscal', 'teste de mcmurray', 'entorse de tornozelo ligamentar',
        'luxacoes e lesoes ligamentares'
    ]) or match_any(topic_norm, ['luxacao', 'lesao ligamentar', 'lesao meniscal', 'lca', 'luxações e lesões ligamentares / meniscais']):
        return "Luxações Articulares e Lesões Ligamentares / Meniscais", 1.0, "Diagnóstico e redução de luxações articulares e propedêutica de lesões ligamentares/meniscais."

    # 31. Tendinopatias, Bursites e Síndromes por Sobrecarga Musculoesquelética
    if match_any(full_norm, [
        'tendinopatia do manguito rotador', 'sindrome do impacto subacromial', 'teste de neer', 'teste de hawkins',
        'epicondilite lateral cotovelo de tenista', 'tenossinovite de de quervain', 'sindrome do tunel do carpo', 'fasceite plantar ortopedica',
        'tendinopatias, bursites e sobrecarga'
    ]) or match_any(topic_norm, ['tendinopatia', 'manguito rotador', 'tunel do carpo', 'epicondilite', 'tendinopatias, bursites e sobrecarga musculoesquelética']):
        return "Tendinopatias, Bursites e Síndromes por Sobrecarga Musculoesquelética", 1.0, "Sobrecargas musculoesqueléticas, tendinopatias e compressões nervosas periféricas."

    # 32. Neoplasias Ósseas Benignas e Sarcomas Ósseos
    if match_any(full_norm, [
        'osteossarcoma', 'sarcoma de ewing', 'triangulo de codman', 'padrao em casca de cebola osseo', 'osteocondroma',
        'cisto osseo simples', 'tumor de celulas gigantes osseo'
    ]) or match_any(topic_norm, ['tumores osseos', 'osteossarcoma', 'sarcoma de ewing']):
        return "Neoplasias Ósseas Benignas e Sarcomas Ósseos", 1.0, "Diagnóstico diferencial radiológico e manejo dos tumores e sarcomas ósseos."

    # 33. Sarcomas de Partes Moles
    if match_any(full_norm, [
        'sarcoma de partes moles', 'lipossarcoma', 'leiomiossarcoma retroperitoneal', 'biopsia percutanea de massa profunda em membro'
    ]) or match_any(topic_norm, ['sarcoma de partes moles', 'tumores de partes moles', 'sarcomas de partes moles']):
        return "Sarcomas de Partes Moles", 1.0, "Investigação diagnóstica e princípios terapêuticos nos sarcomas de partes moles."

    # 34. Emergências Oftalmológicas e Patologias Oculares Frequentes
    if match_any(full_norm, [
        'oftalmologia', 'glaucoma agudo de angulo fechado', 'corpo estranho ocular', 'ulcera de cornea', 'descolamento de retina',
        'oclusao de arteria central da retina', 'uveite anterior', 'conjuntivite', 'hifema traumatico', 'oftalmo'
    ]) or match_any(topic_norm, ['oftalmologia', 'emergencias oftalmologicas', 'glaucoma', 'oftalmo (cm)', 'oftalmo (ped)']):
        return "Emergências Oftalmológicas e Patologias Oculares Frequentes", 1.0, "Urgências e afecções oftalmológicas prevalentes."

    # 35. Trauma Cranioencefálico (TCE) e Hipertensão Intracraniana
    if match_any(full_norm, [
        'trauma cranioencefalico', 'tce', 'escala de coma de glasgow', 'glasgow', 'hematoma extradural', 'hematoma epidural',
        'hematoma subdural agudo', 'lesao axonal difusa', 'lad', 'hipertensao intracraniana no tce', 'pupila midriatica unilateral anisocoria',
        'triade de cushing', 'monitorizacao da pic', 'derrivacao ventricular externa'
    ]) or match_any(topic_norm, ['tce', 'trauma cranioencefalico', 'hematoma subdural', 'hematoma epidural']):
        return "Trauma Cranioencefálico (TCE) e Hipertensão Intracraniana", 1.0, "Manejo agudo do traumatismo cranioencefálico e controle da hipertensão intracraniana."

    # 36. Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco
    if match_any(full_norm, [
        'trauma toracico', 'pneumotorax hipertensivo', 'toracocentese de alivio', 'pneumotorax aberto', 'curativo de tres pontas',
        'hemotorax macico', 'drenagem toracica em selo d agua', 'tamponamento cardiaco no trauma', 'triade de beck',
        'toracotomia de reanimacao na sala de trauma', 'torax instavel', 'contusao pulmonar pos-trauma', 'trauma de torax'
    ]) or match_any(topic_norm, ['trauma toracico', 'pneumotorax', 'hemotorax', 'tamponamento cardiaco', 'trauma de torax']):
        return "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco", 1.0, "Lesões torácicas com risco iminente de morte no trauma."

    # 37. Atendimento Inicial ao Politraumatizado (Protocolo xABCDE)
    if match_any(full_norm, [
        'atendimento inicial ao politraumatizado', 'protocolo xabcde', 'avaliacao primaria no trauma', 'atls 10', 'atls 11',
        'torniquete pre-hospitalar', 'triade letal do trauma', 'protocolo de transfusao macica no trauma', 'acido tranexamico no trauma',
        'fratura de pelve com instabilidade hemodinamica e lencol', 'trauma de pelve'
    ]) or match_any(topic_norm, ['atls', 'politrauma', 'atendimento inicial ao trauma', 'xabcde', 'trauma de pelve', 'trauma', 'choque (cir)']):
        return "Atendimento Inicial ao Politraumatizado (Protocolo xABCDE)", 1.0, "Sistematização do atendimento inicial ao politraumatizado pelo protocolo xABCDE."

    # 38. Trauma Abdominal Fechado e Penetrante (FAST e Laparotomia)
    if match_any(full_norm, [
        'trauma abdominal', 'fast no trauma', 'e-fast', 'trauma esplenico', 'trauma hepatico', 'trauma renal cirurgico',
        'laparotomia exploradora no trauma', 'cirurgia de controle de danos', 'empacotamento hepatico', 'ferimento por arma de fogo abdominal',
        'ferimento por arma branca abdominal', 'figado (cir)'
    ]) or match_any(topic_norm, ['trauma abdominal', 'fast', 'trauma esplenico', 'trauma hepatico', 'controle de danos', 'figado (cir)']):
        return "Trauma Abdominal Fechado e Penetrante (FAST e Laparotomia)", 1.0, "Trauma abdominal contuso/penetrante, conduta não operatória e laparotomia no trauma."

    # 39. Abdome Agudo Perfurativo e Úlcera Péptica Perfurada
    if match_any(full_norm, [
        'abdome agudo perfurativo', 'ulcera perfurada', 'pneumoperitonio', 'sinal de jobert', 'ulcorrafia', 'tampao de graham',
        'perfuracao de viscera oca', 'dor subita em punhalada abdominal'
    ]) or match_any(topic_norm, ['abdome agudo perfurativo', 'ulcera perfurada']):
        return "Abdome Agudo Perfurativo e Úlcera Péptica Perfurada", 1.0, "Quadro clínico, propedêutica e intervenção no abdome agudo perfurativo."

    # 40. Abdome Agudo Vascular e Isquemia Mesentérica
    if match_any(full_norm, [
        'abdome agudo vascular', 'isquemia mesenterica aguda', 'isquemia mesenterica cronica', 'embolia da arteria mesenterica superior',
        'trombose venosa mesenterica', 'colite isquemica', 'angiotomografia mesenterica', 'dor desproporcional ao exame fisico abdominal'
    ]) or match_any(topic_norm, ['abdome agudo vascular', 'isquemia mesenterica']):
        return "Abdome Agudo Vascular e Isquemia Mesentérica", 1.0, "Diagnóstico e condutas no abdome agudo vascular de origem oclusiva arterial e venosa."

    # 41. Abdome Agudo Obstrutivo (Bridas, Neoplasias e Volvo)
    if match_any(full_norm, [
        'abdome agudo obstrutivo', 'obstrucao intestinal mecanica', 'bridas e aderencias', 'volvo de sigmoide', 'volvo de ceco',
        'sinal do grao de cafe radiografia', 'sindrome de ogilvie', 'pseudo-obstrucao colica', 'nivel hidroaereo em escada'
    ]) or match_any(topic_norm, ['abdome agudo obstrutivo', 'obstrucao intestinal', 'volvo de sigmoide']):
        return "Abdome Agudo Obstrutivo (Bridas, Neoplasias e Volvo)", 1.0, "Etiologia, diagnóstico por imagem e manejo do abdome agudo obstrutivo."

    # 42. Abdome Agudo Inflamatório (Apendicite e Diverticulite Aguda)
    if match_any(full_norm, [
        'apendicite aguda', 'apendicectomia laparoscopica', 'sinal de blumberg', 'escore de alvarado', 'diverticulite aguda',
        'classificacao de hinchey', 'apendagite epiploica'
    ]) or match_any(topic_norm, ['apendicite', 'diverticulite', 'abdome agudo inflamatorio', 'abdome agudo']):
        return "Abdome Agudo Inflamatório (Apendicite e Diverticulite Aguda)", 1.0, "Diagnóstico e condutas na apendicite aguda e diverticulite colônica."

    # 43. Litíase Biliar, Colecistite, Coledocolitíase e Colangite
    if match_any(full_norm, [
        'colelitiase', 'colecistite aguda', 'criterios de toquio colecistite', 'coledocolitiase', 'colangite aguda',
        'triade de charcot', 'pentade de reynolds', 'cpre terapeutica', 'colecistectomia videolaparoscopica',
        'colangiografia intraoperatoria', 'colecistostomia percutanea'
    ]) or match_any(topic_norm, ['colecistite', 'coledocolitiase', 'colangite', 'litiase biliar']):
        return "Litíase Biliar, Colecistite, Coledocolitíase e Colangite", 1.0, "Espectro da litíase biliar e complicações infecciosas/obstrutivas das vias biliares."

    # 44. Pancreatites Aguda e Crônica e Pseudocistos Pancreáticos
    if match_any(full_norm, [
        'pancreatite aguda cirurgica', 'criterios de atlanta pancreatite', 'criterios de ranson', 'escore de balthazar',
        'necrose pancreatica infectada', 'pseudocisto pancreatico drenagem', 'pancreatite cronica cirurgia', 'procedimento de frey'
    ]) or match_any(topic_norm, ['pancreatite aguda', 'pancreatite cronica', 'pseudocisto pancreatico']):
        return "Pancreatites Aguda e Crônica e Pseudocistos Pancreáticos", 1.0, "Estratificação de gravidade e tratamento das complicações cirúrgicas pancreáticas."

    # 45. Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)
    if match_any(full_norm, [
        'hernia inguinal indireta', 'hernia inguinal direta', 'hernia femoral', 'hernia crural', 'hernia incisional',
        'hernia umbilical cirurgica', 'hernioplastia inguinal a lichtenstein', 'hernioplastia laparoscopica tapp tep',
        'classificacao de nyhus', 'hernia encarcerada', 'hernia estrangulada'
    ]) or match_any(topic_norm, ['hernia inguinal', 'hernia femoral', 'hernias da parede abdominal', 'hernioplastia']):
        return "Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)", 1.0, "Diagnóstico anatômico, classificação de Nyhus e técnicas de reparo de hérnias abdominais."

    # 46. Técnica Operatória, Diérese, Hemostasia e Síntese (Fios Cirúrgicos)
    if match_any(full_norm, [
        'fio de sutura', 'fio cirurgico', 'poliglactina vicryl', 'nylon sutura', 'polidioxanona pds', 'polipropileno prolene',
        'ponto de donati', 'ponto simples cirurgico', 'sutura intradermica', 'eletrocauterio bisturi eletrico', 'dierese e sintese',
        'anatomia cirurgica'
    ]) or match_any(topic_norm, ['fios cirurgicos', 'tecnica operatoria', 'sutura', 'hemostasia', 'anatomia cirurgica (cir)']):
        return "Técnica Operatória, Diérese, Hemostasia e Síntese (Fios Cirúrgicos)", 1.0, "Propriedades dos fios cirúrgicos, nós e técnicas de síntese tecidual."

    # 47. Avaliação Pré-Operatória e Estratificação de Risco Cirúrgico
    if match_any(full_norm, [
        'avaliacao pre-operatoria', 'estratificacao de risco cirurgico', 'escore asa', 'indice cardiaco revisado de lee',
        'tempo de jejum pre-operatorio acerto eras', 'suspensao de anticoagulantes pre-operatorio', 'suspensao de antiagregantes no perioperatorio',
        'antibioticoprofilaxia cirurgica'
    ]) or match_any(topic_norm, ['pre-operatorio', 'risco cirurgico', 'asa', 'escore de lee', 'jejum pre-operatorio', 'perioperatorio']):
        return "Avaliação Pré-Operatória e Estratificação de Risco Cirúrgico", 1.0, "Estratificação de risco anestésico/cirúrgico e preparo perioperatório baseado em evidências."

    # 48. Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas
    return "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas", 0.95, "Monitorização e conduta nas complicações pós-operatórias (infecção de sítio, febre pós-op, deiscência, íleo paralítico)."

def process_block4(apply=False):
    conn = sqlite3.connect("app/backend/medquest.db")
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT q.id, q.stem, q.topic, q.subtema_orig, q.area, q.subtema, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.area = 'Cirurgia'
        ORDER BY q.id
    """).fetchall()
    
    print(f"==================================================")
    print(f"PROCESSANDO BLOCO 4: CIRURGIA ({len(rows)} QUESTÕES)")
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
        
        new_sub, conf, rationale = classify_cirurgia(q_dict)
        distribution[new_sub] = distribution.get(new_sub, 0) + 1
        
        if old_sub != new_sub:
            changes.append({
                "id": qid,
                "old_subtema": old_sub,
                "new_subtema": new_sub,
                "confidence": conf,
                "rationale": rationale
            })
            
    print(f"\nTotal de reclassificações no Bloco 4: {len(changes)} ({len(changes)/len(rows)*100:.1f}%)")
    print(f"\n--- DISTRIBUIÇÃO DOS 48 SUBTEMAS DO BLOCO 4 ---")
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
        print(f"\n✅ {len(changes)} questões do Bloco 4 atualizadas no banco com sucesso!")
        
    return changes

if __name__ == "__main__":
    apply_flag = "--apply" in sys.argv
    process_block4(apply=apply_flag)
