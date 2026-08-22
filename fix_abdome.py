import codecs

with codecs.open('app/frontend/src/lib/plannerData.ts', 'r', 'utf-8') as f:
    text = f.read()

old_block = '''      {
        "theme": "Abdome Agudo Obstrutivo, Perfurativo e Vascular",
        "highYield": false,
        "dbSubtemas": [
          "Abdome Agudo Obstrutivo",
          "Abdome Agudo Perfurativo",
          "Isquemia Mesentérica",
          "Isquemia Mesentérica Aguda",
          "Obstrução Intestinal por Aderências"
        ],
        "details": [
          "Obstrução alta vs baixa (bridas, volvo, neoplasia, íleo biliar)",
          "Abdome perfurativo (pneumoperitônio, sinal de Jobert)",
          "Isquemia mesentérica aguda: dor desproporcional, acidose e angio-TC",
          "Íleo paralítico pós-operatório e síndrome de Ogilvie"
        ]
      },'''

new_blocks = '''      {
        "theme": "Abdome Agudo Obstrutivo",
        "highYield": false,
        "dbSubtemas": [
          "Abdome Agudo Obstrutivo",
          "Obstrução Intestinal por Aderências"
        ],
        "details": [
          "Obstrução alta vs baixa (bridas, volvo, neoplasia, íleo biliar)",
          "Íleo paralítico pós-operatório e síndrome de Ogilvie"
        ]
      },
      {
        "theme": "Abdome Agudo Perfurativo",
        "highYield": false,
        "dbSubtemas": [
          "Abdome Agudo Perfurativo"
        ],
        "details": [
          "Abdome perfurativo (pneumoperitônio, sinal de Jobert)"
        ]
      },
      {
        "theme": "Abdome Agudo Vascular",
        "highYield": false,
        "dbSubtemas": [
          "Isquemia Mesentérica",
          "Isquemia Mesentérica Aguda"
        ],
        "details": [
          "Isquemia mesentérica aguda: dor desproporcional, acidose e angio-TC"
        ]
      },'''

text = text.replace(old_block, new_blocks)

with codecs.open('app/frontend/src/lib/plannerData.ts', 'w', 'utf-8') as f:
    f.write(text)

print("Replaced Abdome Agudo.")
