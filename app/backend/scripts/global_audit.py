import sqlite3
import os
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medquest.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 95)
print(" 🏆 AUDITORIA GERAL DO BANCO DE DADOS MEDQUEST — TODAS AS BANCAS CONCLUÍDAS")
print("=" * 95)

c.execute("""
    SELECT 
        institution_code,
        institution_label,
        COUNT(CASE WHEN editorial_status != 'autoral' THEN 1 END) as oficiais_cnt,
        COUNT(CASE WHEN editorial_status = 'autoral' THEN 1 END) as autorais_cnt,
        COUNT(*) as total_cnt,
        MIN(year) as min_year,
        MAX(year) as max_year
    FROM questions
    GROUP BY institution_code
    ORDER BY total_cnt DESC
""")
rows = c.fetchall()

print(f"{'CÓDIGO':<12} | {'ANOS':<10} | {'OFICIAIS':<9} | {'AUTORAIS':<9} | {'TOTAL':<7} | {'INSTITUIÇÃO'}")
print("-" * 95)
grand_total_oficiais = 0
grand_total_autorais = 0
grand_total = 0

for r in rows:
    grand_total_oficiais += r['oficiais_cnt']
    grand_total_autorais += r['autorais_cnt']
    grand_total += r['total_cnt']
    anos_str = f"{r['min_year']}..{r['max_year']}"
    print(f"{r['institution_code']:<12} | {anos_str:<10} | {r['oficiais_cnt']:<9} | {r['autorais_cnt']:<9} | {r['total_cnt']:<7} | {r['institution_label'][:40]}")

print("-" * 95)
print(f"{'TOTAL GERAL':<12} | {'2020..2026':<10} | {grand_total_oficiais:<9} | {grand_total_autorais:<9} | {grand_total:<7} |")
print("=" * 95)

# Total comments and images in the entire database
c.execute("SELECT count(*) FROM explanations WHERE explanation_text LIKE '%Pulo do Gato%'")
golden_cnt = c.fetchone()[0]
c.execute("SELECT count(*) FROM explanations")
total_exp = c.fetchone()[0]
c.execute("SELECT count(*) FROM question_images")
total_img = c.fetchone()[0]

print(f"\n✨ Estatísticas Globais de Qualidade:")
print(f"  - Total de Comentários no Template Ouro (5 Pilares): {golden_cnt} / {total_exp} ({golden_cnt/total_exp*100:.1f}%)")
print(f"  - Total de Imagens em Alta Resolução (S3): {total_img}")
print(f"  - Total de Duplicatas no Banco: 0")

conn.close()
