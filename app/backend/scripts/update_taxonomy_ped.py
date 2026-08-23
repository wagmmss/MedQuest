import json

with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    taxonomy = json.load(f)

with open("pediatria_plan_compiled.json", "r", encoding="utf-8") as f:
    ped_plan = json.load(f)

# Built detailed pedagogical curriculum descriptions for the 28 Medway Pediatria modules
ped_module_details = {
    "Desordens do Sistema Imune": [
        "Imunodeficiências primárias (humorais, celulares, combinadas, defeitos de fagócitos e complemento): sinais de alerta",
        "Alergia à proteína do leite de vaca (APLV) IgE-mediada vs não-IgE-mediada e diagnóstico diferencial",
        "Anafilaxia na infância: critérios diagnósticos, manejo imediato com adrenalina intramuscular e orientações",
        "Urticária e angioedema na infância: etiologias e tratamento"
    ],
    "Cardiopatias Congênitas": [
        "Cardiopatias acianogênicas com hiperfluxo pulmonar (CIV, CIA, PCA, DSAV): quadro clínico, sopros característicos e conduta",
        "Cardiopatias acianogênicas com fluxo normal (Coarctação de Aorta, Estenose Aórtica e Pulmonar)",
        "Cardiopatias cianogênicas com hipofluxo (Tetralogia de Fallot, Atresia Pulmonar) e crises de cianose",
        "Cardiopatias cianogênicas com hiperfluxo (Transposição das Grandes Artérias) e teste do coraçãozinho (oximetria de pulso)"
    ],
    "Arritmias, Síncope e PCR": [
        "Taquiarritmias pediátricas: Taquicardia Supraventricular (TSV) estável (manobra vagal, adenosina) vs instável (cardioversão sincronizada)",
        "Bradicardias sintomáticas e bloqueios atrioventriculares na criança",
        "Síncope na infância e adolescência: síncope reflexa/vasovagal vs causas cardíacas de alto risco",
        "Parada Cardiorrespiratória (PCR) pediátrica e algoritmos do PALS (ritmos chocáveis e não chocáveis, compressão e ventilação)"
    ],
    "Constipação Intestinal": [
        "Constipação funcional na infância: critérios de Roma IV e fatores desencadeantes",
        "Diagnóstico diferencial com causas orgânicas (Doença de Hirschsprung/megacólon congênito, hipotireoidismo, fibrose cística)",
        "Manejo do fecaloma e impactação fecal (desimpactação)",
        "Tratamento de manutenção (modificações dietéticas, laxativos osmóticos/PEG) e reeducação esfincteriana"
    ],
    "Síndromes Diarreicas e Disabsortivas": [
        "Diarreia aguda na infância: etiologias virais (Rotavírus, Norovírus) e bacterianas (E. coli, Shigella, Salmonella, Campylobacter)",
        "Avaliação do estado de hidratação e planos de reidratação do Ministério da Saúde (Planos A, B e C)",
        "Terapia de Reidratação Oral (TRO), zinco oral e indicações restritas de antibioticoterapia na diarreia",
        "Diarreia crônica e síndromes disabsortivas: Doença Celíaca e Fibrose Cística (teste do suor)"
    ],
    "Desordens Genéticas e Erros Inatos do Metabolismo": [
        "Principais cromossomopatias: Síndrome de Down (Trissomia 21), Turner (45,X0), Edwards (Trissomia 18) e Patau (Trissomia 13)",
        "Erros Inatos do Metabolismo (EIM): fenilcetonúria, galactosemia, acidemias orgânicas e defeitos do ciclo da ureia",
        "Investigação laboratorial inicial de acidose metabólica grave, hipoglicemia hipocetótica e hiperamonemia no lactente",
        "Glomerulopatias na infância: Síndrome Nefrítica (GNPE) e Síndrome Nefrótica por Lesão Mínima"
    ],
    "Infecção do Trato Urinário (ITU)": [
        "Infecção do trato urinário na infância: fatores de risco, cistite vs pielonefrite aguda",
        "Métodos de coleta de urina conforme controle esfincteriano (saco coletor, cateterismo vesical, punção suprapúbica)",
        "Critérios diagnósticos na urocultura e antibioticoterapia empírica",
        "Investigação por imagem pós-ITU (USG de rins e vias urinárias, ULECT, DMSA) e Refluxo Vesicoureteral (RVU)"
    ],
    "Doenças Exantemáticas": [
        "Diagnóstico diferencial dos exantemas na infância: Sarampo, Rubéola, Exantema Súbito (Roséola / HHV-6), Eritema Infeccioso (Parvovírus B19)",
        "Varicela (Catapora), Escarlatina (Streptococcus pyogenes) e Síndrome Mão-Pé-Boca (Coxsackievirus)",
        "Doença de Kawasaki: critérios diagnósticos clínicos, complicações coronarianas e tratamento com Imunoglobulina venosa + AAS",
        "Complicações, períodos de transmissão, isolamento e condutas pós-exposição"
    ],
    "Imunizações": [
        "Calendário Nacional de Vacinação do PNI da criança e do adolescente",
        "Composição das vacinas (vírus vivos atenuados vs inativadas/recombinantes), vias de administração e aprazamento",
        "Indicações especiais e contraindicações formais das vacinas (BCG, Rotavírus, Febre Amarela, VOP vs VIP)",
        "Centros de Referência para Imunobiológicos Especiais (CRIE) e profilaxias pós-exposição (tétano, raiva, hepatite B, varicela)"
    ],
    "Parasitoses": [
        "Protozooses intestinais: Giardíase e Amebíase (quadro clínico, diagnóstico e tratamento)",
        "Helmintíases comuns: Ascaridíase, Oxiuríase/Enterobíase (prurido anal, fita gomada), Tricocefalíase e Estrongiloidíase",
        "Ancilostomíase e Síndrome de Löeffler (ciclo pulmonar dos helmintos)",
        "Tratamento antiparasitário empírico e profilático e manejo de complicações (obstrução por Ascaris)"
    ],
    "Período Neonatal: Doenças Hematológicas": [
        "Icterícia neonatal fisiológica vs patológica: critérios de hiperbilirrubinemia significante",
        "Incompatibilidade materno-fetal ABO e Rh: testes diagnósticos (Coombs direto, reticulócitos)",
        "Indicações de fototerapia e exsanguineotransfusão (curvas de Bhutani e AAP)",
        "Icterícia do leite materno vs icterícia do aleitamento materno e Doença Hemolítica Perinatal"
    ],
    "Período Neonatal: Doenças Infecciosas": [
        "Sepse neonatal precoce vs tardia: fatores de risco maternos, patógenos comuns (EGB, E. coli, Listeria) e antibioticoterapia empírica",
        "Sífilis congênita: rastreamento materno, estadiamento e conduta completa no recém-nascido sintomático vs exposto",
        "Toxoplasmose congênita: tétrade de Sabin, diagnóstico sorológico e tratamento com Sulfadiazina + Pirimetamina + Ácido Folínico",
        "Citomegalovírus congênito, Rubéola e Zika vírus: quadro clínico e diagnóstico"
    ],
    "Período Neonatal: Doenças do Metabolismo": [
        "Hipoglicemia neonatal: fatores de risco (RN PIG, GIG, prematuros, filhos de mãe diabética), quadro clínico e metas glicêmicas",
        "Hipocalcemia neonatal precoce e tardia: diagnóstico e reposição",
        "Filho de mãe diabética: repercussões metabólicas e estruturais no neonato",
        "Erros inatos com manifestação neonatal aguda no berçário"
    ],
    "Período Neonatal: Doenças Respiratórias": [
        "Síndrome do Desconforto Respiratório / Doença da Membrana Hialina: deficiência de surfactante, fatores de risco e achado radiológico em vidro fosco",
        "Taquipneia Transitória do Recém-Nascido (TTRN): cesariana eletiva sem trabalho de parto, congestão linfática e padrão radiológico",
        "Síndrome de Aspiração Meconial (SAM): fatores de risco (pós-termo), infiltrado algodonoso e complicações (hipertensão pulmonar persistente)",
        "Oxigenoterapia neonatal, CPAP nasal e administração endotraqueal de surfactante exógeno"
    ],
    "Período Neonatal: Doenças Neurológicas e Sensoriais": [
        "Encefalopatia Hipóxico-Isquêmica (EHI): critérios diagnósticos, estadiamento de Sarnat e indicação de hipotermia terapêutica",
        "Hemorragia peri-intraventricular no prematuro: fatores de risco, diagnóstico por USG transfontanelar e prevenção",
        "Convulsões neonatais: diagnóstico diferencial com tremores, etiologias e droga de escolha (Fenobarbital)",
        "Retinopatia da prematuridade e triagem auditiva neonatal (PEATE / emissões otoacústicas)"
    ],
    "Sala de Parto": [
        "Diretrizes de Reanimação do Recém-Nascido em Sala de Parto (SBP): avaliação ao nascimento (termo? respirando/chorando? tônus?)",
        "Passos iniciais da reanimação em recém-nascidos a termo e pré-termo (manter aquecido, posicionar, aspirar se necessário, secar)",
        "Indicações e técnica de Ventilação com Pressão Positiva (VPP) com máscara e balão autoinflável",
        "Massagem cardíaca e uso de Adrenalina/expansores de volume no neonato em sala de parto"
    ],
    "Alojamento Conjunto e Testes de Triagem Neonatal": [
        "Cuidados com o recém-nascido sadio em alojamento conjunto: amamentação, higiene do coto umbilical e orientações de alta",
        "Profilaxia da oftalmia neonatal (Credé/eritromicina) e da doença hemorrágica do recém-nascido (vitamina K intramuscular)",
        "Triagem neonatal biológica (Teste do Pezinho): doenças rastreadas e timing ideal de coleta (3º ao 5º dia de vida)",
        "Triagens neonatais sensoriais e funcionais: Teste do Olhinho (reflexo vermelho), Teste da Orelhinha, Teste do Coraçãozinho e Teste da Linguinha"
    ],
    "Epilepsia e Síndromes Convulsivas": [
        "Convulsão febril na infância: classificação em simples vs complexa, conduta na crise e prognóstico benigno",
        "Manejo farmacológico do estado de mal epiléptico na emergência pediátrica (Benzodiazepínicos, Fenitoína, Levetiracetam)",
        "Principais síndromes epilépticas da infância: Síndrome de West (espasmos epilépticos, hipsarritmia), Síndrome de Lennox-Gastaut",
        "Crises de ausência típica infantil e epilepsia mioclônica juvenil"
    ],
    "Distúrbios Carenciais": [
        "Anemia ferropriva na infância: fisiopatologia, diagnóstico laboratorial (ferritina, ferro sérico, hemograma microcítico e hipocrômico)",
        "Diretrizes de suplementação profilática e terapêutica de ferro elementar segundo a SBP e Ministério da Saúde",
        "Raquitismo carencial por deficiência de vitamina D: manifestações clínicas e radiológicas (rosário raquítico, alargamento epifisário)",
        "Outras carências de micronutrientes: hipovitaminose A, escorbuto (vitamina C) e deficiência de zinco"
    ],
    "Nutrição na Pediatria": [
        "Aleitamento materno exclusivo até os 6 meses e complementar até os 2 anos ou mais: benefícios e técnica de pega correta",
        "Dificuldades na amamentação: fissuras mamilares, ingurgitamento mamário, mastite e contraindicações formais ao aleitamento",
        "Alimentação complementar saudável: introdução alimentar, consistência e variedade",
        "Desnutrição energético-proteica na infância (Marasmo vs Kwashiorkor) e Obesidade infantil: avaliação e manejo"
    ],
    "Nariz, Ouvido e Laringe": [
        "Otite Média Aguda (OMA): agentes bacterianos, diagnóstico otoscópico e critérios de antibioticoterapia empírica (Amoxicilina)",
        "Faringoamigdalite bacteriana (S. pyogenes): escore de Centor, teste rápido para estreptococo e prevenção de Febre Reumática",
        "Sinusite bacteriana aguda na infância: critérios clínicos de complicação e tratamento",
        "Laringotraqueobronquite aguda (Crupe viral) e Epiglotite aguda: diagnóstico diferencial de estridor na emergência"
    ],
    "Distúrbios Obstrutivos": [
        "Asma na infância: diagnóstico clínico, classificação de gravidade e tratamento de manutenção conforme diretrizes GINA",
        "Manejo da crise asmática aguda na emergência: broncodilatadores inalatórios de curta ação, corticoides sistêmicos e oxigenoterapia",
        "Bronquiolite Viral Aguda (BVA): fisiopatologia pelo VSR, diagnóstico clínico, suporte de oxigênio/hidratação e profilaxia com Palivizumabe",
        "Aspiração de corpo estranho em vias aéreas: manifestação clínica, achados radiológicos e broncoscopia"
    ],
    "Segurança e Violência na Infância": [
        "Maus-tratos e violência contra a criança e o adolescente: violência física, psicológica, negligência e violência sexual",
        "Sinais de alerta no exame físico (lesões incompatíveis com a história, fraturas em diferentes estágios de consolidação, síndrome do bebê sacudido)",
        "Papel do médico, notificação compulsória obrigatória ao Conselho Tutelar e medidas de proteção",
        "Prevenção de acidentes domésticos na infância: sufocação, quedas, queimaduras, intoxicações e afogamento"
    ],
    "Avaliação e Transtornos do Comportamento na Infância e Adolescência": [
        "Transtorno do Espectro Autista (TEA): sinais precoces de alerta no lactente (contato visual, atenção compartilhada, M-CHAT)",
        "Transtorno de Déficit de Atenção e Hiperatividade (TDAH): critérios diagnósticos e abordagem multidisciplinar",
        "Transtornos do sono na infância: higiene do sono, terror noturno e sonambulismo",
        "Saúde mental do adolescente: depressão, automutilação e ideação suicida"
    ],
    "Distúrbios Estaturais e Puberais": [
        "Investigação sistemática da baixa estatura: variantes normais (baixa estatura familiar vs atraso constitucional do crescimento) vs patológicas",
        "Avaliação do alvo genético parental, idade óssea (RX de punho e mão) e velocidade de crescimento",
        "Puberdade precoce central (GnRH-dependente) vs periférica (GnRH-independente): estadiamento de Tanner e conduta",
        "Puberdade atrasada no menino e na menina: causas hipogonadotróficas e hipergonadotróficas"
    ],
    "Crescimento e Desenvolvimento na Infância e Adolescência": [
        "Puericultura sistemática: monitorização do crescimento infantil pelas curvas da OMS (peso/idade, estatura/idade, IMC/idade, PC/idade)",
        "Interpretação de escores-Z e percentis de crescimento",
        "Marcos do Desenvolvimento Neuropsicomotor (DNPM): motor grosso, motor fino-adaptativo, linguagem e pessoal-social",
        "Reflexos primitivos (Moro, sucção, preensão palmar/plantar, tônico-cervical assimétrico) e sua época de desaparecimento"
    ],
    "Sepse, Choque Séptico e Outros tipos de Choque": [
        "Reconhecimento precoce de Sepse e Choque Séptico na emergência pediátrica (Surviving Sepsis Campaign Pediátrica)",
        "Pacote da primeira hora: obtenção de acesso venoso/intraósseo, ressuscitação volêmica guiada por metas e antibioticoterapia precoce",
        "Choque quente vs choque frio e drogas vasoativas de escolha (Adrenalina, Noradrenalina, Milrinona)",
        "Choque anafilático na criança: reconhecimento imediato e manejo com Adrenalina IM"
    ],
    "Vasculites": [
        "Vasculite por IgA (Púrpura de Henoch-Schönlein): tétrade clássica (púrpura palpável não trombocitopênica, artrite/artralgia, dor abdominal e nefropatia)",
        "Diagnóstico clínico, indicação de corticoterapia nas complicações gastrointestinais e seguimento renal",
        "Doença de Kawasaki (revisão de aspectos vasculíticos e aneurismas de coronária)",
        "Artrite Idiopática Juvenil (AIJ) e febre de origem indeterminada na infância"
    ]
}

new_ped_macro = []
for item in ped_plan:
    name = item["name"]
    high_yield = item["high_yield"]
    details = ped_module_details.get(name, [name])
    
    new_ped_macro.append({
        "theme": name,
        "highYield": high_yield,
        "dbSubtemas": [name],
        "details": details
    })

# Find Pediatria area in taxonomy
ped_index = -1
for i, area_data in enumerate(taxonomy):
    area_name = area_data.get("area", "")
    if "Pediatria" in area_name:
        ped_index = i
        break

if ped_index >= 0:
    taxonomy[ped_index]["macroThemes"] = new_ped_macro
    print(f"Replaced Pediatria with {len(new_ped_macro)} Medway macro-themes!")
else:
    taxonomy.append({
        "area": "Pediatria",
        "macroThemes": new_ped_macro
    })
    print("Added Pediatria to taxonomy!")

with open("app/backend/data/taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(taxonomy, f, ensure_ascii=False, indent=2)

print("Saved updated taxonomy.json for Pediatria!")
