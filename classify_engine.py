import json
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")

with open('canonical_taxonomy_170.json', encoding='utf-8') as f:
    tax = json.load(f)

CANONICAL_THEMES = {}
for area, themes in tax.items():
    for t in themes:
        CANONICAL_THEMES[t] = area

def norm(text):
    text = unicodedata.normalize('NFD', str(text or ''))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().strip()

def match_any(text, patterns):
    for p in patterns:
        if re.search(r'\b' + p + r'\b', text):
            return True
    return False

def classify_question(q):
    stem = q.get('stem', '')
    alts = q.get('alternatives', '')
    exp = q.get('explanation', '')
    topic = q.get('topic', '')
    subtema_orig = q.get('current_subtema', '')
    
    full_text = f"{stem} {alts} {exp} {topic}"
    full_norm = norm(full_text)
    stem_norm = norm(stem)
    topic_norm = norm(topic)
    exp_norm = norm(exp)

    # 1. Fournier gangrene & Necrotizing soft tissue infections & Pressure ulcers & Degloving
    if match_any(full_norm, ['gangrena de fournier', 'fournier', 'fasceite necrosante', 'fasceite necrotizante', 'infeccao necrosante', 'morel-lavallee', 'ferimento descolante', 'degloving', 'lesao por pressao', 'curativo por pressao negativa', 'enxerto de pele', 'enxertia de pele', 'emagrecimento da pele descolada']):
        if not match_any(full_norm, ['apendicite', 'diverticulite']):
            return "Cirurgia", "Cicatrização, Tratamento de Feridas, Enxertos e Retalhos", "Fisiologia da cicatrização, enxertos, retalhos e infecções necrosantes de partes moles."

    # 2. Pediatric Burns
    if match_any(full_norm, ['queimadura', 'queimado', 'queimaduras', 'escaldo', 'escaldadura']) and match_any(stem_norm, ['lactente', 'meses de vida', 'recem-nascido', 'crianca de 1 ano', 'crianca de 2 ano', 'crianca de 3 ano', 'menino de 1 ano', 'menino de 2 ano', 'menina de 1 ano', 'menina de 2 ano']):
        return "Cirurgia", "Particularidades das Queimaduras na Faixa Etária Pediátrica", "Particularidades do manejo e reposição volêmica em queimaduras na faixa etária pediátrica."

    # 3. Adult/General Burns
    if match_any(full_norm, ['queimadura', 'queimado', 'queimaduras', 'superficie corporal queimada', 'scq', 'escarotomia', 'flictena', 'flictenas', 'grau de queimadura', 'parkland']) and not match_any(full_norm, ['marjolin', 'cicatriz antiga de queimadura']):
        return "Cirurgia", "Atendimento ao Paciente Queimado e Reposição Volêmica", "Atendimento inicial, classificação de profundidade e ressuscitação volêmica do paciente queimado."

    # 4. Marjolin ulcer & Cutaneous Oncology
    if match_any(full_norm, ['marjolin', 'carcinoma espinocelular cutaneo', 'carcinoma basocelular', 'melanoma', 'breslow', 'linfonodo sentinela', 'clark', 'cbc', 'cec cutaneo']):
        if not match_any(full_norm, ['parotida', 'lingua', 'laringe', 'canal anal', 'esofago']):
            return "Cirurgia", "Oncologia Cutânea: Melanoma, CBC e CEC", "Neoplasias malignas da pele (Melanoma, CBC, CEC e Úlcera de Marjolin)."

    # 5. Polipose Adenomatosa Familiar (PAF) e Síndromes Hereditárias
    if match_any(full_norm, ['polipose adenomatosa familiar', 'paf', 'sindrome de lynch', 'hnpcc', 'peutz-jeghers', 'gardner', 'turcot', 'incontaveis polipos']):
        return "Cirurgia", "Polipose Adenomatosa Familiar (PAF) e Síndromes Hereditárias", "Síndromes hereditárias de polipose intestinal e câncer colorretal familiar (PAF e Lynch)."

    # 6. Câncer de Pulmão, Nódulo Pulmonar Solitário e Tumores do Mediastino
    if match_any(full_norm, ['nodulo pulmonar solitario', 'timoma', 'tumor de mediastino', 'massa no mediastino', 'miastenia gravis', 'cancer de pulmao', 'carcinoma broncogenico', 'lobectomia pulmonar']) and not match_any(full_norm, ['trauma', 'hemotorax', 'pneumotorax hipertensivo']):
        return "Cirurgia", "Câncer de Pulmão, Nódulo Pulmonar Solitário e Tumores do Mediastino", "Nódulo pulmonar solitário, estadiamento do câncer de pulmão e neoplasias do mediastino (Timoma)."

    # 7. Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)
    if match_any(full_norm, ['adenocarcinoma gastrico', 'cancer gastrico', 'cancer de estomago', 'linfadenectomia d2', 'adenocarcinoma de colon', 'cancer de colon', 'cancer colorretal', 'cancer de reto', 'mesorreto', 'adenocarcinoma de pancreas', 'cancer de pancreas', 'whipple', 'duodenopancreatectomia', 'gist gastrico', 'cancer de esofago', 'ipmn', 'neoplasia mucinosa papilar intraductal']):
        if not match_any(full_norm, ['diverticulite', 'apendicite', 'pancreatite aguda biliar', 'coledocolitiase', 'cpre']):
            return "Cirurgia", "Neoplasias do Trato Gastrointestinal (Esôfago, Estômago, Pâncreas e Cólon)", "Diagnóstico, estadiamento e tratamento cirúrgico das neoplasias do trato gastrointestinal."

    # 8. Abordagem Cirúrgica das Doenças Inflamatórias Intestinais (Crohn e RCU)
    if match_any(full_norm, ['doenca de crohn', 'retocolite ulcerativa', 'rcu', 'proctocolectomia total com bolsa ileal', 'estrituroplastia', 'megacolon toxico']):
        return "Cirurgia", "Abordagem Cirúrgica das Doenças Inflamatórias Intestinais (Crohn e RCU)", "Manejo e indicações cirúrgicas na Doença de Crohn e Retocolite Ulcerativa."

    # 9. Distúrbios Motores do Esôfago, Megaesôfago e Síndrome Disfágica
    if match_any(full_norm, ['acalasia', 'megaesofago', 'rezende', 'heller', 'cardiomiotomia', 'dilatacao pneumatica', 'diverticulo de zenker', 'espasmo esofagiano difuso', 'sindrome disfagica']):
        return "Cirurgia", "Distúrbios Motores do Esôfago, Megaesôfago e Síndrome Disfágica", "Distúrbios da motilidade esofágica, megaesôfago e divertículos esofágicos."

    # 10. Doença do Refluxo Gastroesofágico (DRGE) e Úlcera Péptica
    if match_any(full_norm, ['drge', 'refluxo gastroesofagico', 'fundoplicatura', 'nissen', 'hernia de hiato', 'esofago de barrett', 'barrett']) and not match_any(full_norm, ['perfurada', 'hematemese', 'hda']):
        return "Cirurgia", "Doença do Refluxo Gastroesofágico (DRGE) e Úlcera Péptica", "Quadro clínico, seguimento de Esôfago de Barrett e cirurgia antirrefluxo na DRGE."

    # 11. Hemorragia Digestiva Alta e Baixa na Emergência Cirúrgica
    if match_any(full_norm, ['hemorragia digestiva alta', 'hda', 'hematemese', 'melena', 'forrest', 'varizes esofagicas', 'sengstaken', 'hemorragia digestiva baixa', 'hdb', 'hematoquezia macica']):
        return "Cirurgia", "Hemorragia Digestiva Alta e Baixa na Emergência Cirúrgica", "Abordagem de emergência, estabilização hemodinâmica e conduta na hemorragia digestiva alta e baixa."

    # 12. Cirurgia Bariátrica e Metabólica
    if match_any(full_norm, ['cirurgia bariatrica', 'bypass gastrico', 'bypass em y de roux', 'gastrectomia vertical', 'sleeve', 'fistula gastrojejunal', 'hernia interna pos bariatrica', 'estenose da gastroenteroanastomose', 'estenose de anastomose pos bariatrica']):
        return "Cirurgia", "Cirurgia Bariátrica e Metabólica", "Indicações cirúrgicas, técnicas e manejo de complicações pós-operatórias na cirurgia bariátrica."

    # 13. Cirurgia Pediátrica e Malformações Digestivas Neonatais
    if match_any(full_norm, ['estenose hipertrofica do piloro', 'atresia de esofago', 'fistula traqueoesofagica', 'hernia diafragmatica congenita', 'bochdalek', 'morgagni', 'atresia duodenal', 'ma rotacao intestinal', 'volvo de intestino medio', 'hirschsprung', 'anomalia anorretal', 'imperfuracao anal', 'onfalocele', 'gastrosquise', 'atresia biliar', 'kasai', 'intussuscepcao ileocolica', 'invaginacao intestinal', 'fecaloma na crianca', 'hipotermia no recem-nascido']):
        return "Cirurgia", "Cirurgia Pediátrica e Malformações Digestivas Neonatais", "Malformações congênitas neonatais e patologias cirúrgicas pediátricas."

    # 14. Cirurgia de Cabeça e Pescoço: Afecções Cervicais Benignas e Cistos Congênitos
    if match_any(full_norm, ['cisto tireoglosso', 'sistrunk', 'cisto branquial', 'higroma cistico', 'adenoma pleomorfico', 'warthin', 'parotidectomia', 'glandula parotida', 'biopsia de linfonodo cervical', 'triangulo cervical', 'nivel vb', 'nivel iv']):
        if not match_any(full_norm, ['carcinoma papilifero', 'bethesda', 'carcinoma medular']):
            return "Cirurgia", "Cirurgia de Cabeça e Pescoço: Afecções Cervicais Benignas e Cistos Congênitos", "Afecções cervicais congênitas, massas benignas de pescoço e patologias de glândulas salivares."

    # 15. Neoplasias de Cabeça e Pescoço e Nódulos Tireoidianos Cirúrgicos
    if match_any(full_norm, ['nodulo tireoidiano', 'carcinoma papilifero', 'carcinoma folicular', 'carcinoma medular', 'bethesda', 'tireoidectomia', 'cancer de laringe', 'cancer de lingua', 'cancer de orofaringe', 'carcinoma epidermoide de cabeca e pescoco', 'esvaziamento cervical']):
        return "Cirurgia", "Neoplasias de Cabeça e Pescoço e Nódulos Tireoidianos Cirúrgicos", "Nódulos tireoidianos cirúrgicos, câncer de tireoide e carcinomas espinocelulares de cabeça e pescoço."

    # 16. Coloproctologia: Doenças Orificiais e Afecções Colorretais
    if match_any(full_norm, ['hemorroida', 'hemorroidectomia', 'doenca hemorroidaria', 'trombose hemorroidaria', 'fissura anal', 'abscesso perianal', 'fistula perianal', 'fistula anorretal', 'goodsall', 'cisto pilonidal', 'cancer de canal anal', 'carcinoma espinocelular de canal anal']):
        return "Cirurgia", "Coloproctologia: Doenças Orificiais e Afecções Colorretais", "Doenças orificiais benignas e malignas anorretais (hemorroidas, fissuras, abscessos, fístulas e CEC anal)."

    # 17. Uro-Oncologia: Câncer de Próstata, Rim, Bexiga e Testículo
    if match_any(full_norm, ['cancer de prostata', 'psa', 'biopsia de prostata', 'prostatectomia', 'cancer de rim', 'carcinoma de celulas renais', 'angiomiolipoma', 'cancer de bexiga', 'rtu de bexiga', 'cancer de testiculo', 'orquiectomia', 'escroto agudo', 'torcao testicular', 'sinal de prehn', 'massa testicular', 'tumor de testiculo', 'neoplasia testicular']):
        return "Cirurgia", "Uro-Oncologia: Câncer de Próstata, Rim, Bexiga e Testículo", "Uro-oncologia (próstata, rim, bexiga, testículo) e propedêutica do escroto agudo."

    # 18. Hiperplasia Prostática Benigna (HPB) e Litíase Urinária
    if match_any(full_norm, ['hiperplasia prostatica benigna', 'hpb', 'litiase urinaria', 'nefrolitiase', 'calculo renal', 'calculo ureteral', 'leco', 'ureterolitotripsia', 'rtu de prostata']):
        return "Cirurgia", "Hiperplasia Prostática Benigna (HPB) e Litíase Urinária", "Manejo clínico e cirúrgico da HPB e intervenções na litíase urinária."

    # 19. Aneurismas de Aorta Abdominal e Torácica
    if match_any(full_norm, ['aneurisma de aorta', 'aneurisma da aorta', 'aneurisma abdominal infra-renal', 'disseccao de aorta', 'disseccao aortica', 'stanford a', 'stanford b', 'evar']):
        return "Cirurgia", "Aneurismas de Aorta Abdominal e Torácica", "Diagnóstico, critérios de intervenção e tratamento cirúrgico/endovascular de aneurismas e dissecções aórticas."

    # 20. Doença Arterial Obstrutiva Periférica e Oclusões Arteriais Agudas
    if match_any(full_norm, ['doenca arterial obstrutiva periferica', 'daop', 'claudicacao intermitente', 'isquemia critica', 'indice tornozelo-braco', 'itb', 'oclusao arterial aguda', 'embolia arterial', 'trombose arterial aguda', 'cateter de fogarty', 'tromboembolectomia', 'revascularizacao arterial']):
        return "Cirurgia", "Doença Arterial Obstrutiva Periférica e Oclusões Arteriais Agudas", "Quadro clínico, exames de imagem e condutas na DAOP crônica e na oclusão arterial aguda."

    # 21. Insuficiência Venosa Crônica e Trombose Venosa Profunda (TVP)
    if match_any(full_norm, ['trombose venosa profunda', 'tvp', 'tromboembolismo venoso', 'tev', 'insuficiencia venosa cronica', 'varizes', 'ulcera venosa', 'tromboprofilaxia']):
        return "Cirurgia", "Insuficiência Venosa Crônica e Trombose Venosa Profunda (TVP)", "Diagnóstico, escores de risco, profilaxia e anticoagulação na TVP e insuficiência venosa crônica."

    # 22. Cirurgia Cardíaca: Revascularização Miocárdica e Cirurgia Valvar
    if match_any(full_norm, ['revascularizacao miocardica', 'ponte de safena', 'arteria mamaria', 'troca valvar mitral', 'troca valvar aortica', 'circulacao extracorporea']) and not match_any(full_norm, ['apendicite', 'diverticulite']):
        return "Cirurgia", "Cirurgia Cardíaca: Revascularização Miocárdica e Cirurgia Valvar", "Princípios da cirurgia de revascularização miocárdica e cirurgias orovalvares."

    # 23. Cirurgia Torácica Geral e Doenças Pleurais
    if match_any(full_norm, ['empiema pleural', 'derrame pleural parapneumonico', 'decorticacao pleuropulmonar', 'pneumotorax espontaneo', 'fistula broncopleural', 'estenose traqueal', 'estenose subglotica', 'traqueostomia']) and not match_any(full_norm, ['trauma toracico', 'ferimento por arma']):
        return "Cirurgia", "Cirurgia Torácica Geral e Doenças Pleurais", "Patologias pleurais infecciosas, pneumotórax espontâneo e cirurgia das vias aéreas centrais."

    # 24. Fundamentos da Anestesiologia, Farmacologia e Bloqueios
    if match_any(full_norm, ['anestesiologia', 'anestesia geral', 'raquianestesia', 'anestesia peridural', 'bloqueador neuromuscular', 'succinilcolina', 'rocuronio', 'sugamadex', 'lidocaina', 'bupivacaina', 'anestesico local sem vasoconstritor', 'anestesico local', 'toxicidade por anestesico local']):
        if match_any(full_norm, ['vasoconstritor', 'anestesia', 'anestesico', 'bloqueio']):
            return "Cirurgia", "Fundamentos da Anestesiologia, Farmacologia e Bloqueios", "Farmacologia anestésica, uso seguro de anestésicos locais e bloqueios regionais."

    # 25. Trauma de Face e Pescoço (Trauma Cervical e Fraturas Maxilofaciais)
    if match_any(full_norm, ['trauma cervical', 'ferimento cervical', 'zona i do pescoco', 'zona ii do pescoco', 'zona iii do pescoco', 'platisma', 'fratura de le fort', 'le fort', 'fratura de mandibula', 'fratura zigomatica', 'fratura nasal', 'trauma maxilofacial', 'trauma de face', 'blow-out', 'blowout']):
        return "Cirurgia", "Trauma de Face e Pescoço (Trauma Cervical e Fraturas Maxilofaciais)", "Trauma cervical contuso/penetrante e fraturas maxilofaciais."

    # 26. Trauma Raquimedular (TRM) e Lesões Vertebrais
    if match_any(full_norm, ['trauma raquimedular', 'trm', 'choque medular', 'choque neurogenico', 'fratura de chance', 'brown-sequard', 'sindrome medular']):
        return "Cirurgia", "Trauma Raquimedular (TRM) e Lesões Vertebrais", "Avaliação diagnóstica e condutas no trauma raquimedular e lesões da coluna vertebral."

    # 27. Trauma Ortopédico de Extremidades e Síndrome Compartimental
    if match_any(full_norm, ['sindrome compartimental', 'fasciotomia', 'pressao intracompartimental']) or (match_any(full_norm, ['trauma vascular', 'lesao de arteria']) and match_any(full_norm, ['membro', 'coxa', 'perna', 'braco', 'fratura'])):
        return "Cirurgia", "Trauma Ortopédico de Extremidades e Síndrome Compartimental", "Trauma grave de membros, síndrome compartimental e lesões vasculares associadas."

    # 28. Fraturas Ósseas e Princípios Gerais de Osteossíntese
    if match_any(full_norm, ['fratura exposta', 'gustilo', 'osteossintese', 'placa e parafuso', 'haste intramedular', 'fixador externo', 'consolidacao ossea', 'pseudoartrose', 'fratura do colo do femur', 'fratura de tibia', 'fratura de radio', 'fratura diafisaria']):
        return "Cirurgia", "Fraturas Ósseas e Princípios Gerais de Osteossíntese", "Classificação, princípios biológicos de consolidação e métodos de osteossíntese de fraturas ósseas."

    # 29. Trauma Cranioencefálico (TCE) e Hipertensão Intracraniana
    if match_any(full_norm, ['trauma cranioencefalico', 'tce', 'hematoma extradural', 'hematoma epidural', 'hematoma subdural', 'lesao axonal difusa', 'hipertensao intracraniana', 'anisocoria', 'pupila midriatica', 'monro-kellie', 'craniossinostose', 'cranioestenose', 'escafocefalia', 'plagiocefalia']):
        return "Cirurgia", "Trauma Cranioencefálico (TCE) e Hipertensão Intracraniana", "Manejo agudo do traumatismo cranioencefálico, hipertensão intracraniana e craniossinostoses."

    # 30. Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco
    if match_any(full_norm, ['pneumotorax hipertensivo', 'pneumotorax aberto', 'hemotorax macico', 'tamponamento cardiaco', 'triade de beck', 'toracostomia', 'drenagem de torax', 'torax instavel', 'contusao pulmonar', 'trauma toracico', 'fratura de costelas', 'fraturas de arcos costais']):
        return "Cirurgia", "Trauma Torácico: Pneumotórax, Hemotórax e Tamponamento Cardíaco", "Diagnóstico e condutas de urgência no trauma torácico (pneumotórax, hemotórax, tamponamento, contusão)."

    # 31. Atendimento Inicial ao Politraumatizado (Protocolo xABCDE)
    if match_any(full_norm, ['atendimento inicial ao politraumatizado', 'xabcde', 'protocolo de transfusao macica', 'triade letal', 'triade da morte', 'choque no trauma', 'fratura de bacia instavel', 'avaliacao primaria no trauma', 'atls']):
        return "Cirurgia", "Atendimento Inicial ao Politraumatizado (Protocolo xABCDE)", "Sistematização do atendimento inicial ao politraumatizado pelo protocolo xABCDE e ressuscitação hemodinâmica."

    # 32. Trauma Abdominal Fechado e Penetrante (FAST e Laparotomia)
    if match_any(full_norm, ['trauma abdominal', 'fast', 'e-fast', 'trauma esplenico', 'trauma hepatico', 'trauma renal', 'trauma pancreatico', 'controle de danos', 'laparotomia no trauma', 'ferimento por arma de fogo no abdome', 'ferimento por arma branca no abdome', 'trauma toracoabdominal']):
        return "Cirurgia", "Trauma Abdominal Fechado e Penetrante (FAST e Laparotomia)", "Abordagem do trauma abdominal contuso e penetrante, indicações cirúrgicas e tratamento não operatório."

    # 33. Abdome Agudo Perfurativo e Úlcera Péptica Perfurada
    if match_any(full_norm, ['ulcera perfurada', 'ulcera gastrica perfurada', 'abdome agudo perfurativo', 'pneumoperitonio', 'jobert', 'ulcorrafia', 'tampao de graham']):
        return "Cirurgia", "Abdome Agudo Perfurativo e Úlcera Péptica Perfurada", "Diagnóstico e manejo cirúrgico do abdome agudo perfurativo por úlcera péptica."

    # 34. Abdome Agudo Vascular e Isquemia Mesentérica
    if match_any(full_norm, ['isquemia mesenterica aguda', 'isquemia mesenterica cronica', 'embolia de arteria mesenterica', 'trombose venosa mesenterica', 'colite isquemica', 'abdome agudo vascular', 'angina mesenterica']):
        return "Cirurgia", "Abdome Agudo Vascular e Isquemia Mesentérica", "Diagnóstico clínico, angiográfico e conduta nas diferentes apresentações de isquemia mesentérica."

    # 35. Abdome Agudo Obstrutivo (Bridas, Neoplasias e Volvo)
    if match_any(full_norm, ['abdome agudo obstrutivo', 'obstrucao intestinal', 'obstrucao de delgado', 'obstrucao de colon', 'bridas', 'volvo de sigmoide', 'volvo de ceco', 'sindrome de ogilvie', 'pseudo-obstrucao colica', 'grao de cafe', 'u invertido', 'hematoma da bainha do reto']):
        return "Cirurgia", "Abdome Agudo Obstrutivo (Bridas, Neoplasias e Volvo)", "Etiologia, diagnóstico por imagem e manejo clínico/cirúrgico das obstruções intestinais mecânicas e funcionais."

    # 36. Abdome Agudo Inflamatório (Apendicite e Diverticulite Aguda)
    if match_any(full_norm, ['apendicite aguda', 'apendicectomia', 'diverticulite aguda', 'hinchey', 'apendagite epiploica', 'abscesso periapendicular', 'plastrao apendicular', 'abdome agudo inflamatorio']):
        return "Cirurgia", "Abdome Agudo Inflamatório (Apendicite e Diverticulite Aguda)", "Diagnóstico clínico/tomográfico e condutas na apendicite aguda e diverticulite colônica."

    # 37. Litíase Biliar, Colecistite, Coledocolitíase e Colangite
    if match_any(full_norm, ['colelitiase', 'colecistite aguda', 'criterios de tokyo', 'coledocolitiase', 'colangite aguda', 'charcot', 'reynolds', 'cpre', 'colecistectomia', 'colangiografia intraoperatoria', 'colangioressonancia', 'colecistostomia']):
        return "Cirurgia", "Litíase Biliar, Colecistite, Coledocolitíase e Colangite", "Litíase biliar e complicações infecciosas/obstrutivas das vias biliares."

    # 38. Pancreatites Aguda e Crônica e Pseudocistos Pancreáticos
    if match_any(full_norm, ['pancreatite aguda', 'atlanta', 'ranson', 'balthazar', 'necrose pancreatica', 'pseudocisto pancreatico', 'pancreatite cronica']):
        return "Cirurgia", "Pancreatites Aguda e Crônica e Pseudocistos Pancreáticos", "Diagnóstico, estratificação de gravidade e tratamento das pancreatites aguda e crônica."

    # 39. Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)
    if match_any(full_norm, ['hernia inguinal', 'hernia femoral', 'hernia crural', 'hernia incisional', 'hernia umbilical', 'hernia epigastrica', 'hernia de spiegel', 'hernioplastia', 'herniorrafia', 'lichtenstein', 'tapp', 'tep', 'anel inguinal']):
        return "Cirurgia", "Hérnias da Parede Abdominal (Inguinais, Femorais e Incisionais)", "Diagnóstico anatômico, indicações cirúrgicas e técnicas de reparo de hérnias da parede abdominal."

    # 40. Técnica Operatória, Diérese, Hemostasia e Síntese (Fios Cirúrgicos)
    if match_any(full_norm, ['fio cirurgico', 'fio de sutura', 'vicryl', 'nylon', 'monocryl', 'pds', 'prolene', 'catgut', 'ponto de donati', 'ponto simples', 'ponto continuo', 'ponto intradermico', 'bisturi eletrico', 'dierese', 'hemostasia', 'sintese']):
        return "Cirurgia", "Técnica Operatória, Diérese, Hemostasia e Síntese (Fios Cirúrgicos)", "Fundamentos de técnica cirúrgica, propriedades dos fios e técnicas de síntese tecidual."

    # 41. Avaliação Pré-Operatória e Estratificação de Risco Cirúrgico
    if match_any(full_norm, ['avaliacao pre-operatoria', 'risco cirurgico', 'asa', 'escore de lee', 'goldman', 'jejum pre-operatorio', 'acerto', 'eras', 'antibioticoprofilaxia', 'suspensao de medicamento']):
        return "Cirurgia", "Avaliação Pré-Operatória e Estratificação de Risco Cirúrgico", "Avaliação de risco cirúrgico/anestésico e preparo pré-operatório."

    # 42. Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas
    if match_any(full_norm, ['pos-operatorio', 'complicacao pos-operatoria', 'infeccao de sitio cirurgico', 'isc', 'deiscencia', 'febre no pos-operatorio', 'atelectasia', 'ileo paralitico', 'dreno cirurgico', 'dreno']):
        return "Cirurgia", "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas", "Monitorização e manejo de intercorrências e complicações pós-operatórias."

    # Fallback to current if canonical Cirurgia theme
    if subtema_orig in CANONICAL_THEMES and CANONICAL_THEMES[subtema_orig] == "Cirurgia":
        return "Cirurgia", subtema_orig, f"Tema cirúrgico canônico validado ({subtema_orig})."

    return "Cirurgia", "Manejo Pós-Operatório e Tratamento de Complicações Cirúrgicas", "Classificação cirúrgica geral."
