import sqlite3
import asyncio
import os
from libsql_client import create_client

TURSO_URL = "https://medquest-wagmss.aws-us-east-1.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODYyMjYzMjUsImlkIjoiMDE5ZmUzNjItNmUwMS03YTE5LTkyZjctMGRhOTJlZTk5OWQ0Iiwia2lkIjoiTlhsOWVXamdJaXcwVW5vNmhSTGdhSVFsRl9OaVBxSm13eHB6U21hY1hNUSIsInJpZCI6IjJhMjVkMzQ0LWI3ZTctNDA5YS1hMmIzLTVlNWNkMTgxMWE4NCJ9.jOZcgW1n4dCGN1W8SPG-vMFpj734oh0Wn1NDl7lteH6NsD5nqeOXmr1tZm4TEQVhTO-_2aN29LBz1u7o29D1Dw"
LOCAL_DB = "medquest.db"

async def migrate():
    print("Conectando ao banco local...")
    local = sqlite3.connect(LOCAL_DB)
    
    print("Conectando ao Turso...")
    turso = create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)

    # Pegar o schema de todas as tabelas
    cursor = local.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    
    for name, sql in tables:
        print(f"Criando tabela {name} no Turso...")
        try:
            await turso.execute(f"DROP TABLE IF EXISTS {name}")
        except Exception:
            pass
        await turso.execute(sql)
        
        # Inserir os dados
        cursor.execute(f"SELECT * FROM {name}")
        rows = cursor.fetchall()
        
        if not rows:
            continue
            
        print(f"Inserindo {len(rows)} linhas na tabela {name}...")
        
        # Pegar os nomes das colunas
        cursor.execute(f"PRAGMA table_info({name})")
        cols = [col[1] for col in cursor.fetchall()]
        placeholders = ", ".join(["?"] * len(cols))
        
        insert_sql = f"INSERT INTO {name} ({', '.join(cols)}) VALUES ({placeholders})"
        
        # Batch insert
        batch_size = 100
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            statements = []
            for row in batch:
                # Convert tuple to list and handle bytes if any
                clean_row = [x if not isinstance(x, bytes) else x.decode('utf-8', 'ignore') for x in row]
                statements.append({"sql": insert_sql, "args": clean_row})
            try:
                await turso.batch(statements)
            except Exception as e:
                print(f"Erro no lote {i}: {e}")
                import traceback
                traceback.print_exc()
                break
            
    print("Migração concluída com sucesso!")
    await turso.close()

if __name__ == "__main__":
    asyncio.run(migrate())
