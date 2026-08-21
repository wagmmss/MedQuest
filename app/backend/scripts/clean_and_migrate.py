import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medquest.db")
MIGRATION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations", "004_fts5.sql")

def run_cleanup_and_migration():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("Iniciando limpeza...")
    # Identificar IDs para deletar
    cur.execute("""
        SELECT id FROM questions 
        WHERE institution_code IS NULL 
           OR institution_code = 'instituição não identificada' 
           OR institution_label LIKE '%não identificada%'
           OR missing_alts = 1
    """)
    ids_to_delete = [row['id'] for row in cur.fetchall()]
    
    if ids_to_delete:
        print(f"Deletando {len(ids_to_delete)} questões inválidas e suas dependências...")
        # Deletar dependências (já que não há garantia de ON DELETE CASCADE no schema original)
        placeholders = ','.join('?' for _ in ids_to_delete)
        
        cur.execute(f"DELETE FROM alternatives WHERE question_id IN ({placeholders})", ids_to_delete)
        print(f"  - {cur.rowcount} alternatives removidas.")
        
        cur.execute(f"DELETE FROM question_images WHERE question_id IN ({placeholders})", ids_to_delete)
        print(f"  - {cur.rowcount} question_images removidas.")
        
        cur.execute(f"DELETE FROM explanations WHERE question_id IN ({placeholders})", ids_to_delete)
        print(f"  - {cur.rowcount} explanations removidas.")
        
        cur.execute(f"DELETE FROM attempts WHERE question_id IN ({placeholders})", ids_to_delete)
        print(f"  - {cur.rowcount} attempts removidas.")
        
        cur.execute(f"DELETE FROM favorites WHERE question_id IN ({placeholders})", ids_to_delete)
        print(f"  - {cur.rowcount} favorites removidas.")
        
        cur.execute(f"DELETE FROM spaced_repetition WHERE question_id IN ({placeholders})", ids_to_delete)
        print(f"  - {cur.rowcount} spaced_repetition removidas.")
        
        cur.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", ids_to_delete)
        print(f"  - {cur.rowcount} questions removidas.")
    else:
        print("Nenhuma questão para limpar.")
    
    # Criar FTS5
    print("\nAplicando migração FTS5...")
    with open(MIGRATION_FILE, "r", encoding="utf-8") as f:
        sql = f.read()
    
    # Executa a migração (script bloqueia se tabela já existir devido ao IF NOT EXISTS, exceto INSERT)
    # Para garantir idempotência no script Python em caso de re-execução, vamos limpar a tabela FTS se ela já existir
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions_fts'")
    if cur.fetchone():
        print("Aviso: questions_fts já existe. Deletando para recriar...")
        cur.execute("DROP TABLE questions_fts")
    
    cur.executescript(sql)
    print("Migração FTS5 aplicada com sucesso!")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_cleanup_and_migration()
