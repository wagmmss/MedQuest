import json
import os

# Load RENAMING mapping
from rename_and_clean_all import RENAMING

# Load taxonomy to get areas and high-yield status
with open("app/backend/data/taxonomy.json", "r", encoding="utf-8") as f:
    tax = json.load(f)

# Build comprehensive de-para structure
de_para_by_area = {}
de_para_flat = []

# Reverse lookup or direct area scan
area_order = ["Clínica Médica", "Cirurgia", "Ginecologia e Obstetrícia", "Pediatria", "Medicina Preventiva"]

# Create inverse map for reverse lookup (new -> old)
new_to_old = {v: k for k, v in RENAMING.items()}

for area_data in tax:
    area = area_data["area"]
    de_para_by_area[area] = []
    
    for macro in area_data.get("macroThemes", []):
        new_theme = macro["theme"]
        old_theme = new_to_old.get(new_theme, new_theme)
        is_high_yield = macro.get("highYield", False)
        
        item = {
            "area": area,
            "nome_original": old_theme,
            "nome_novo": new_theme,
            "foco_usp_high_yield": is_high_yield
        }
        de_para_by_area[area].append(item)
        de_para_flat.append(item)

# 1. Save JSON file
os.makedirs("app/backend/data", exist_ok=True)
json_path = "app/backend/data/de_para_temas.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({
        "total_temas": len(de_para_flat),
        "areas": de_para_by_area
    }, f, ensure_ascii=False, indent=2)

print(f"Saved {json_path} with {len(de_para_flat)} entries!")

# 2. Save Markdown documentation file
os.makedirs("docs", exist_ok=True)
md_path = "docs/de_para_temas.md"

md_lines = [
    "# 📑 Tabela De/Para: Mapeamento e Renomeação dos Módulos Médicos",
    "",
    "> **Objetivo**: Este documento registra a relação direta entre a nomenclatura original e os novos títulos técnicos personalizados da plataforma MedQuest, preservando 100% da temática, escopo clínico e carga horária de cada aula.",
    "",
    f"**Total de Módulos Estruturados**: {len(de_para_flat)} temas distribuídos nas 5 grandes áreas médicas.",
    "",
    "---",
    ""
]

for area in area_order:
    items = de_para_by_area.get(area, [])
    hy_count = sum(1 for x in items if x["foco_usp_high_yield"])
    
    md_lines.append(f"## 🩺 {area} ({len(items)} temas | {hy_count} Foco USP 🔥)")
    md_lines.append("")
    md_lines.append("| # | Nome Original | Novo Nome Personalizado (MedQuest) | Foco USP 🔥 |")
    md_lines.append("|---|---|---|:---:|")
    
    for i, item in enumerate(items, 1):
        foco = "🔥 Sim" if item["foco_usp_high_yield"] else "Não"
        md_lines.append(f"| {i:02d} | {item['nome_original']} | **{item['nome_novo']}** | {foco} |")
    
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

print(f"Saved {md_path} with full side-by-side tables!")
