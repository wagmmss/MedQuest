import os
import sqlite3

import libsql_client


def sync():
    print("Conectando ao SQLite local...")
    local_conn = sqlite3.connect('medquest.db')
    local_c = local_conn.cursor()
    
    # Pegar todas as explanations
    explanations = local_c.execute("SELECT question_id, explanation_text, generated_at FROM explanations").fetchall()
    print(f"Total de explicações locais: {len(explanations)}")
    
    print("Conectando ao Turso...")
    url = os.environ.get("TURSO_DATABASE_URL")
    token = os.environ.get("TURSO_AUTH_TOKEN")
    client = libsql_client.create_client_sync(url=url, auth_token=token)
    
    # Verificar quantas já existem no Turso
    turso_count = client.execute("SELECT COUNT(*) FROM explanations").rows[0][0]
    print(f"Total de explicações no Turso antes do sync: {turso_count}")
    
    batch_size = 50
    queries = []
    inserted = 0
    
    print("Iniciando sincronização...")
    for row in explanations:
        sql = "REPLACE INTO explanations (question_id, explanation_text, generated_at) VALUES (?, ?, ?)"
        queries.append(libsql_client.Statement(sql, list(row)))
        
        if len(queries) >= batch_size:
            client.batch(queries)
            inserted += len(queries)
            print(f"Sincronizados {inserted} / {len(explanations)}")
            queries = []
            
    if queries:
        client.batch(queries)
        inserted += len(queries)
        print(f"Sincronizados {inserted} / {len(explanations)}")
        
    print("Sincronização concluída com sucesso!")
    
if __name__ == "__main__":
    sync()
