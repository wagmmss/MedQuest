"""
Classificador de Alta Precisão - Bloco 2: Pediatria (28 Subtemas Canônicos)
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

def classify_pediatria(q):
    stem = q.get('stem', '')
    alts = q.get('alternatives', '')
    exp = q.get('explanation', '')
    topic = q.get('topic', '')
    subtema_orig = q.get('subtema_orig', '')
    
    stem_norm = norm(stem)
    topic_norm = norm(topic)
    sub_orig_norm = norm(subtema_orig)
    full_norm = norm(f"{stem} {topic} {subtema_orig}")

    # 1. Reanimação Neonatal e Assistência em Sala de Parto
    if match_any(full_norm, [
        'reanimacao neonatal', 'passos iniciais da reanimacao', 'ventilacao com pressao positiva', 'vpp em sala de parto',
        'clampagem tardia do cordao', 'clampagem do cordao', 'escore de apgar', 'boletim de apgar', 'sala de parto',
        'aspiracao de vias aereas em sala de parto', 'massagem cardiaca neonatal', 'adrenalina em sala de parto'
    ]) or match_any(topic_norm, ['reanimacao neonatal', 'sala de parto', 'apgar']):
        return "Reanimação Neonatal e Assistência em Sala de Parto", 1.0, "Reanimação neonatal em sala de parto e assistência imediata ao recém-nascido."

    # 2. Alojamento Conjunto e Testes de Triagem Neonatal
    if match_any(full_norm, [
        'teste do pezinho', 'teste do olhinho', 'teste do coracaozinho', 'teste da orelhinha', 'teste da linguinha',
        'triagem neonatal', 'alojamento conjunto', 'reflexo vermelho ocular', 'oximetria de pulso no rn',
        'emissao otoacustica', 'teste de triagem neonatal'
    ]) or match_any(topic_norm, ['triagem neonatal', 'alojamento conjunto', 'teste do pezinho', 'triagem']):
        return "Alojamento Conjunto e Testes de Triagem Neonatal (Pezinho, Olhinho, Coraçãozinho)", 1.0, "Triagem neonatal biológica e reflexos de rastreamento no alojamento conjunto."

    # 3. Neonatologia: Asfixia Perinatal, Encefalopatia e Doenças Neurológicas
    if match_any(full_norm, [
        'asfixia perinatal', 'encefalopatia hipoxico-isquemica', 'sarnat', 'hipotermia terapeutica neonatal',
        'hemorragia peri-intraventricular', 'hemorragia intraventricular neonatal', 'leucomalacia periventricular'
    ]) or match_any(topic_norm, ['asfixia perinatal', 'encefalopatia hipoxico-isquemica', 'asfixia']):
        return "Neonatologia: Asfixia Perinatal, Encefalopatia e Doenças Neurológicas", 1.0, "Asfixia perinatal, encefalopatia hipóxico-isquêmica e lesões neurológicas do neonato."

    # 4. Neonatologia: Desconforto Respiratório e Doença da Membrana Hialina
    if match_any(full_norm, [
        'doenca da membrana hialina', 'sindrome do desconforto respiratorio do rn', 'surfactante pulmonar',
        'taquipneia transitoria do recem-nascido', 'ttrn', 'sindrome de aspiracao meconial', 'sam',
        'displasia broncopulmonar', 'silberman-anderson', 'silverman anderson', 'boletim de silverman'
    ]) or match_any(topic_norm, ['desconforto respiratorio do rn', 'membrana hialina', 'ttrn', 'aspiracao meconial', 'respiratorio neonatal']):
        return "Neonatologia: Desconforto Respiratório e Doença da Membrana Hialina", 1.0, "Patologias respiratórias neonatais (Membrana Hialina, TTRN, SAM)."

    # 5. Neonatologia: Infecções Congênitas (TORCH) e Sepse Neonatal
    if match_any(full_norm, [
        'infeccao congenita', 'torch', 'toxoplasmose congenita', 'sifilis congenita', 'rubeola congenita',
        'citomegalovirus congenito', 'cmv congenito', 'herpes neonatal', 'sepse neonatal precoce', 'sepse neonatal tardia',
        'coriorretinite', 'calcificacoes periventriculares', 'calcificacoes intracranianas difusas', 'surdez neurossensorial congenita'
    ]) or match_any(topic_norm, ['torch', 'sifilis congenita', 'toxoplasmose congenita', 'sepse neonatal', 'infeccoes congenitas']):
        return "Neonatologia: Infecções Congênitas (TORCH) e Sepse Neonatal", 1.0, "Infecções congênitas do grupo TORCH e sepse neonatal."

    # 6. Neonatologia: Icterícia Neonatal e Doenças Hematológicas
    if match_any(full_norm, [
        'ictericia neonatal', 'ictericia fisiologica', 'ictericia pelo leite materno', 'ictericia do aleitamento',
        'fototerapia neonatal', 'exsanguineotransfusao', 'zona de kramer', 'incompatibilidade abo', 'incompatibilidade rh neonatal',
        'kernicterus', 'bilirrubina indireta no rn', 'policitemia neonatal', 'doenca hemolitica perinatal'
    ]) or match_any(topic_norm, ['ictericia neonatal', 'fototerapia', 'incompatibilidade rh/abo', 'ictericia']):
        return "Neonatologia: Icterícia Neonatal e Doenças Hematológicas", 1.0, "Icterícia neonatal fisiológica/patológica e distúrbios hematológicos do neonato."

    # 7. Neonatologia: Distúrbios Metabólicos e Hipoglicemia no Recém-Nascido
    if match_any(full_norm, [
        'hipoglicemia neonatal', 'filho de mae diabetica', 'hipocalcemia neonatal', 'hipomagnesemia neonatal',
        'glicemia capilar no rn', 'rn giga', 'macrossomia neonatal'
    ]) or match_any(topic_norm, ['hipoglicemia neonatal', 'filho de mae diabetica', 'disturbios metabolicos do rn']):
        return "Neonatologia: Distúrbios Metabólicos e Hipoglicemia no Recém-Nascido", 1.0, "Distúrbios metabólicos e glicêmicos do recém-nascido."

    # 8. Calendário Vacinal do PNI e Imunizações Especiais
    if match_any(full_norm, [
        'calendario vacinal', 'pni', 'programa nacional de imunizacoes', 'vacina bcg', 'vacina hepatite b',
        'vacina pentavalente', 'vacina vop', 'vacina vip', 'vacina rotavirus', 'vacina pneumococica 10',
        'vacina meningococica c', 'vacina meningo acwy', 'vacina febre amarela', 'vacina triplice viral',
        'vacina tetraviral', 'vacina varicela', 'vacina dtp', 'vacina hpv', 'crie', 'imunobiologicos especiais'
    ]) or match_any(topic_norm, ['vacina', 'imunizacao', 'pni', 'calendario vacinal', 'vacinacao']):
        return "Calendário Vacinal do PNI e Imunizações Especiais", 1.0, "Calendário nacional de vacinação e imunobiológicos especiais (CRIE)."

    # 9. Doenças Exantemáticas e Diagnóstico Diferencial dos Exantemas
    if match_any(full_norm, [
        'sarampo', 'manchas de koplik', 'rubeola', 'manchas de forchheimer', 'eritema infeccioso', 'parvovirus b19',
        'face esbofeteada', 'exantema subito', 'roseola infantum', 'herpes-virus humano 6', 'varicela', 'catapora',
        'escarlatina', 'sinal de filatow', 'sinal de pastia', 'lingua em framboesa', 'doenca mao-pe-boca', 'coxsackie',
        'mononucleose infecciosa', 'doenca do beijo', 'exantema maculopapular na infancia'
    ]) or match_any(topic_norm, ['exantematicas', 'sarampo', 'varicela', 'escarlatina', 'rubeola', 'exantemas']):
        return "Doenças Exantemáticas e Diagnóstico Diferencial dos Exantemas", 1.0, "Diagnóstico diferencial e conduta nas doenças exantemáticas infantis."

    # 10. Vasculites na Infância e Febre Reumática
    if match_any(full_norm, [
        'doenca de kawasaki', 'kawasaki', 'aneurisma de coronaria', 'gamaglobulina venosa', 'purpura de henoch-schonlein',
        'purpura por iga', 'vasculite por iga', 'artrite na infancia com purpura palpavel', 'intussuscepcao por henoch',
        'febre reumatica', 'criterios de jones', 'coreia de sydenham', 'cardite reumatica', 'eritema marginado'
    ]) or match_any(topic_norm, ['kawasaki', 'henoch-schonlein', 'vasculites na infancia', 'febre reumatica']):
        return "Vasculites na Infância (Henoch-Schönlein e Kawasaki)", 1.0, "Vasculites pediátricas (Kawasaki e Púrpura de Henoch-Schönlein) e febre reumática."

    # 11. Afecções de Vias Aéreas Superiores: OMA, Sinusite e Faringoamigdalite
    if match_any(full_norm, [
        'otite media aguda', 'oma', 'faringoamigdalite', 'faringite estreptococica', 'streptococcus pyogenes',
        'sinusite bacteriana aguda na crianca', 'laringite estridulosa', 'crup viral', 'crupe', 'laringotraqueobronquite',
        'epiglotite aguda', 'sinal do polegar', 'sinal da torre', 'abscesso periamigdaliano', 'abscesso retrofaringeo'
    ]) or match_any(topic_norm, ['otite', 'oma', 'faringite', 'crup', 'crupe', 'laringite', 'sinusite ped', 'ivas']):
        return "Afecções de Vias Aéreas Superiores: OMA, Sinusite e Faringoamigdalite", 1.0, "Infecções e obstruções agudas de vias aéreas superiores na infância."

    # 12. Distúrbios Obstrutivos, Asma e Bronquiolite na Infância
    if match_any(full_norm, [
        'bronquiolite viral aguda', 'bva', 'virus sincicial respiratorio', 'vsr', 'asma na crianca', 'asma infantil',
        'lactente sibilante', 'bebe chiador', 'fibrose cistica', 'teste do suor', 'broncodilatador de curta',
        'escore de gravidade de bronquiolite', 'palivizumabe', 'pneumonia adquirida na comunidade ped',
        'pneumonia complicada', 'derrame pleural parapneumonico ped'
    ]) or match_any(topic_norm, ['bronquiolite', 'asma', 'manutencao - asma', 'exacerbacao - asma', 'lactente sibilante', 'fibrose cistica', 'pneumonia adquirida na comunidade (ped)', 'pneumonia complicada (ped)']):
        return "Distúrbios Obstrutivos, Asma e Bronquiolite na Infância", 1.0, "Doenças obstrutivas e infecciosas pulmonares da infância (BVA, Asma, PAC pediátrica e Fibrose Cística)."

    # 13. Diarreia Aguda, Reidratação Oral e Doenças Disabsortivas
    if match_any(full_norm, [
        'diarreia aguda', 'gastroenterite aguda', 'tro', 'terapia de reidratacao oral', 'plano a de hidratacao',
        'plano b de hidratacao', 'plano c de hidratacao', 'desidratacao grave na crianca', 'zinco na diarreia',
        'doenca celiaca na crianca', 'sindrome disabsortiva', 'diarreia cronica infantil', 'intolerancia a lactose',
        'invaginacao intestinal', 'intussuscepcao'
    ]) or match_any(topic_norm, ['diarreia aguda', 'reidratacao', 'desidratacao infantil', 'doenca celiaca ped', 'invaginacao intestinal (ped)']):
        return "Diarreia Aguda, Reidratação Oral e Doenças Disabsortivas", 1.0, "Diarreia aguda, planos de hidratação e doenças disabsortivas na infância."

    # 14. Parasitoses Intestinais: Helmintíases e Protozooses
    if match_any(full_norm, [
        'ascaris lumbricoides', 'ascaridiase', 'sindrome de loeffler', 'enterobius vermicularis', 'oxiurose',
        'prurido anal noturno', 'fita gomada', 'giardia lamblia', 'giardiase', 'entamoeba histolytica', 'amebiase',
        'ancilostomiase', 'necator americanus', 'strongyloides stercoralis', 'estrongiloidiase', 'schistosoma mansoni',
        'esquistossomose', 'albendazol', 'mebendazol', 'metronidazol parasitose'
    ]) or match_any(topic_norm, ['parasitoses', 'helmintos', 'protozoarios', 'ascaris', 'giardia']):
        return "Parasitoses Intestinais: Helmintíases e Protozooses", 1.0, "Helmintíases e protozooses intestinais na infância."

    # 15. Constipação Intestinal Funcional e Orgânica
    if match_any(full_norm, [
        'constipacao intestinal infantil', 'constipacao funcional', 'criterios de roma iv crianca',
        'fecaloma na crianca', 'encoprese', 'escape fecal', 'peg 4000', 'polietilenoglicol', 'hirschsprung'
    ]) or match_any(topic_norm, ['constipacao infantil', 'encoprese', 'constipacao']):
        return "Constipação Intestinal Funcional e Orgânica", 1.0, "Constipação intestinal funcional e diagnóstico diferencial de causas orgânicas."

    # 16. Infecção do Trato Urinário (ITU), Nefrologia e Refluxo Vesicoureteral na Infância
    if match_any(full_norm, [
        'infeccao do trato urinario na crianca', 'itu na infancia', 'pielonefrite aguda infantil', 'refluxo vesicoureteral',
        'rvu', 'uretrocistografia miccional', 'ucgm', 'dmsa', 'cintilografia com dmsa', 'valvula de uretra posterior', 'vup',
        'sindrome nefrotica', 'lesao minima', 'hematuria glomerular na crianca', 'gnda', 'gnpe', 'sindrome hemolitico uremica',
        'shu', 'hipertensao arterial ped'
    ]) or match_any(topic_norm, ['itu ped', 'refluxo vesicoureteral', 'itu na infancia', 'sindrome nefrotica (ped)', 'sindrome hemolitico uremica (ped)', 'infeccao de trato urinario (ped)']):
        return "Infecção do Trato Urinário (ITU) e Refluxo Vesicoureteral na Infância", 1.0, "Nefropatias pediátricas, ITU e refluxo vesicoureteral."

    # 17. Anemias Carenciais e Distúrbios de Micronutrientes
    if match_any(full_norm, [
        'anemia ferropriva na infancia', 'suplementacao de ferro profilatica', 'profilaxia com ferro elemental',
        'raquitismo', 'deficiencia de vitamina d', 'escorbuto', 'deficiencia de vitamina a', 'xeroftalmia',
        'ferritina baixa na crianca', 'microcitose e hipocromia ped'
    ]) or match_any(topic_norm, ['anemia ferropriva ped', 'suplementacao de ferro', 'raquitismo', 'vitaminas ped', 'anemias carenciais']):
        return "Anemias Carenciais e Distúrbios de Micronutrientes (Ferro, Vitamina D)", 1.0, "Anemias carenciais (ferropriva) e deficiências de micronutrientes na infância."

    # 18. Aleitamento Materno, Alimentação Complementar e Desnutrição Infantil
    if match_any(full_norm, [
        'aleitamento materno exclusivo', 'ame', 'pega correta na amamentacao', 'fissura mamilar', 'ingurgitamento mamario',
        'alimentacao complementar', 'introducao alimentar', 'desnutricao infantil', 'kwashiorkor', 'marasma',
        'desnutricao grave', 'edema carencial', 'formula infantil'
    ]) or match_any(topic_norm, ['aleitamento materno', 'amamentacao', 'alimentacao complementar', 'desnutricao infantil', 'tecnica e dificuldades no am (ped)']):
        return "Aleitamento Materno, Alimentação Complementar e Desnutrição Infantil", 1.0, "Manejo da amamentação, alimentação saudável e desnutrição energético-proteica."

    # 19. Baixa Estatura, Puberdade Precoce e Atraso Puberal
    if match_any(full_norm, [
        'baixa estatura', 'baixa estatura familiar', 'retardo constitucional do crescimento e puberdade', 'rccp',
        'idade ossea', 'velocidade de crescimento', 'alvo parental', 'puberdade precoce', 'adrenarca precoce',
        'telarca precoce', 'estadiamento de tanner', 'tanner m', 'tanner g', 'tanner p', 'hipotireoidismo congenito', 'pan-hipopituitarismo'
    ]) or match_any(topic_norm, ['baixa estatura', 'tanner', 'puberdade precoce', 'puberdade (ped)', 'crescimento', 'endocrino (ped)']):
        return "Baixa Estatura, Puberdade Precoce e Atraso Puberal", 1.0, "Investigação da baixa estatura e avaliação dos distúrbios da puberdade (Tanner)."

    # 20. Puericultura: Marcos do Desenvolvimento (DNPM) e Curvas de Crescimento
    if match_any(full_norm, [
        'marcos do desenvolvimento', 'dnpm', 'desenvolvimento neuropsicomotor', 'curvas de crescimento oms',
        'escore z', 'peso para idade', 'estatura para idade', 'imc para idade', 'perimetro cefalico',
        'puericultura', 'reflexos primitivos', 'moro', 'tonico assimetrico do pescoco', 'sustentacao da cabeca',
        'sentar sem apoio', 'andar sozinho', 'pinca fina'
    ]) or match_any(topic_norm, ['puericultura', 'dnpm', 'marcos do desenvolvimento (ped)', 'curvas oms', 'classificacao imc (ped)', 'obesidade (ped)', 'saude da crianca']):
        return "Puericultura: Marcos do Desenvolvimento (DNPM) e Curvas de Crescimento", 1.0, "Acompanhamento do DNPM, reflexos arcaicos e curvas de crescimento infantil da OMS."

    # 21. Convulsão Febril, Epilepsias e Síndromes Convulsivas na Infância
    if match_any(full_norm, [
        'convulsao febril', 'convulsao febril simples', 'convulsao febril complexa', 'sindrome de west',
        'espasmos infantis', 'hipsarritmia', 'crise de ausencia na infancia', 'epilepsia mioclonica juvenil',
        'crise epileptica pediatrica', 'diazepam retal'
    ]) or match_any(topic_norm, ['convulsao febril', 'epilepsia ped', 'sindrome de west', 'convulsoes na emergencia (ped)']):
        return "Convulsão Febril, Epilepsias e Síndromes Convulsivas na Infância", 1.0, "Crises convulsivas na infância (Convulsão Febril e Epilepsias da Infância)."

    # 22. Cardiopatias Congênitas Cianogênicas e Acianogênicas
    if match_any(full_norm, [
        'cardiopatia congenita', 'tetralogia de fallot', 'crise de cianose', 'transposicao das grandes arterias',
        'tga', 'comunicacao interventricular', 'civ', 'comunicacao interatrial', 'cia', 'persistência do canal arterial',
        'pca', 'coarctacao de aorta ped', 'sopro cardiaco na crianca', 'fluxo pulmonar aumentado'
    ]) or match_any(topic_norm, ['cardiopatias congenitas', 'tetralogia de fallot', 'civ', 'cia', 'pca', 'cardiopatia']):
        return "Cardiopatias Congênitas Cianogênicas e Acianogênicas", 1.0, "Cardiopatias congênitas acianogênicas e cianogênicas."

    # 23. Arritmias, Síncope e Parada Cardiorrespiratória Pediátrica (PALS)
    if match_any(full_norm, [
        'pals', 'parada cardiorrespiratoria pediatrica', 'suporte avancado de vida em pediatria',
        'taquicardia supraventricular na crianca', 'tsv na crianca', 'manobra vagal crianca', 'adenosina ped',
        'desfibrilacao pediatrica', 'adrenalina no pals', 'bradicardia sintomatica ped'
    ]) or match_any(topic_norm, ['pals', 'pcr pediatrica', 'arritmias pediatricas', 'parada cardiorrespiratoria (ped)']):
        return "Arritmias, Síncope e Parada Cardiorrespiratória Pediátrica (PALS)", 1.0, "Ressuscitação cardiopulmonar pediátrica (PALS) e emergências arrítmicas."

    # 24. Sepse Pediátrica, Choque e Ressuscitação Hemodinâmica
    if match_any(full_norm, [
        'sepse pediatrica', 'choque septico pediatrico', 'ressuscitaçao volemica pediatrica', 'expansao com cristaloide 20 ml/kg',
        'choque frio', 'choque quente', 'adrenalina no choque septico ped', 'noradrenalina ped'
    ]) or match_any(topic_norm, ['sepse pediatrica', 'choque septico ped', 'sepse (ped)', 'emergencias pediatricas (ped)']):
        return "Sepse Pediátrica, Choque e Ressuscitação Hemodinâmica", 1.0, "Sepse grave, choque e ressuscitação hemodinâmica pediátrica."

    # 25. Genética Médica, Cromossomopatias e Erros Inatos do Metabolismo
    if match_any(full_norm, [
        'sindrome de down', 'trissomia do 21', 'sindrome de turner', 'sindrome de klinefelter',
        'sindrome de edwards', 'sindrome de patau', 'erro inato do metabolismo', 'fenilcetonuria',
        'galactosemia', 'mucopolissacaridose', 'tumor de wilms'
    ]) or match_any(topic_norm, ['genetica', 'cromossomopatias', 'down', 'turner', 'erros inatos']):
        return "Genética Médica, Cromossomopatias e Erros Inatos do Metabolismo", 1.0, "Genética médica pediátrica, cromossomopatias e erros inatos do metabolismo."

    # 26. Transtornos do Neurodesenvolvimento e Saúde Mental na Infância
    if match_any(full_norm, [
        'transtorno do espectro autista', 'tea', 'tdah na crianca', 'transtorno de deficit de atencao e hiperatividade',
        'metilfenidato ped', 'atraso global do desenvolvimento', 'depressao infantil', 'ansiedade na infancia'
    ]) or match_any(topic_norm, ['autismo', 'tea', 'tdah ped', 'saude mental infantil', 'tdah (ped)']):
        return "Transtornos do Neurodesenvolvimento (TEA, TDAH) e Saúde Mental na Infância", 1.0, "Transtornos do neurodesenvolvimento (TEA, TDAH) e saúde mental pediátrica."

    # 27. Segurança Infantil, Prevenção de Acidentes e Maus-Tratos
    if match_any(full_norm, [
        'maus-tratos infantis', 'maus tratos na infancia', 'abuso sexual infantil', 'sindrome do bebe sacudido',
        'violencia contra crianca', 'notificacao ao conselho tutelar', 'prevencao de acidentes na infancia',
        'afogamento infantil', 'intoxicacao exogena infantil', 'aspiracao de corpo estranho ped', 'queimadura ped prevencao'
    ]) or match_any(topic_norm, ['maus-tratos', 'acidentes infantis', 'conselho tutelar', 'maus tratos e violencia (ped)', 'intoxicacoes exogenas (ped)', 'ingestao e aspiracao de corpo estranho, brue (ped)']):
        return "Segurança Infantil, Prevenção de Acidentes e Maus-Tratos", 1.0, "Prevenção de acidentes infantis, segurança e manejo de suspeita de maus-tratos."

    # 28. Imunodeficiências, Alergias e Anafilaxia na Infância
    if match_any(full_norm, [
        'anafilaxia infantil', 'adrenalina intramuscular na anafilaxia', 'alergia a proteina do leite de vaca', 'aplv',
        'dermatite atopica', 'alergia alimentar ped', 'imunodeficiencia primaria', 'agaglobulinemia ligada ao x',
        'imunodeficiencia comum variavel', 'sindrome de digeorge'
    ]) or match_any(topic_norm, ['anafilaxia ped', 'aplv', 'imunodeficiencias', 'anafilaxia (ped)']):
        return "Imunodeficiências, Alergias e Anafilaxia na Infância", 1.0, "Alergias alimentares (APLV), anafilaxia e imunodeficiências congênitas."

    # Default fallback
    return "Puericultura: Marcos do Desenvolvimento (DNPM) e Curvas de Crescimento", 0.90, "Puericultura e acompanhamento pediátrico geral."

def process_block2(apply=False):
    conn = sqlite3.connect("app/backend/medquest.db")
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT q.id, q.stem, q.topic, q.subtema_orig, q.area, q.subtema, e.explanation_text
        FROM questions q
        LEFT JOIN explanations e ON q.id = e.question_id
        WHERE q.area = 'Pediatria'
        ORDER BY q.id
    """).fetchall()
    
    print(f"==================================================")
    print(f"PROCESSANDO BLOCO 2: PEDIATRIA ({len(rows)} QUESTÕES)")
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
        
        new_sub, conf, rationale = classify_pediatria(q_dict)
        distribution[new_sub] = distribution.get(new_sub, 0) + 1
        
        if old_sub != new_sub:
            changes.append({
                "id": qid,
                "old_subtema": old_sub,
                "new_subtema": new_sub,
                "confidence": conf,
                "rationale": rationale
            })
            
    print(f"\nTotal de reclassificações no Bloco 2: {len(changes)} ({len(changes)/len(rows)*100:.1f}%)")
    print(f"\n--- DISTRIBUIÇÃO DOS 28 SUBTEMAS DO BLOCO 2 ---")
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
        print(f"\n✅ {len(changes)} questões do Bloco 2 atualizadas no banco com sucesso!")
        
    return changes

if __name__ == "__main__":
    apply_flag = "--apply" in sys.argv
    process_block2(apply=apply_flag)
