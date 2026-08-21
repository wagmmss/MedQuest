import os

# Load env
from dotenv import load_dotenv

load_dotenv()

import libsql_client


def rebuild():
    url = os.environ.get("TURSO_DATABASE_URL")
    token = os.environ.get("TURSO_AUTH_TOKEN")
    
    if not url or not token:
        print("Missing TURSO env vars")
        return
        
    url = url.replace("libsql://", "https://")
    client = libsql_client.create_client_sync(url=url, auth_token=token)
    
    print("Dropping old FTS triggers...")
    triggers = [
        "trg_questions_fts_ins", "trg_questions_fts_upd", "trg_questions_fts_del",
        "trg_explanations_fts_ins", "trg_explanations_fts_upd", "trg_explanations_fts_del"
    ]
    for t in triggers:
        try:
            client.execute(f"DROP TRIGGER IF EXISTS {t}")
        except Exception:
            pass
            
    print("Dropping old FTS table...")
    try:
        client.execute("DROP TABLE IF EXISTS questions_fts")
    except Exception as e:
        print("Error dropping:", e)
        # Turso might throw error, we try dropping backing tables manually
        try:
            client.execute("DROP TABLE IF EXISTS questions_fts_data")
            client.execute("DROP TABLE IF EXISTS questions_fts_idx")
            client.execute("DROP TABLE IF EXISTS questions_fts_content")
            client.execute("DROP TABLE IF EXISTS questions_fts_docsize")
            client.execute("DROP TABLE IF EXISTS questions_fts_config")
        except Exception:
            pass

    print("Recreating FTS table...")
    with open("migrations/004_fts5.sql", "r") as f:
        sql = f.read()
        
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                client.execute(stmt)
            except Exception as e:
                print(f"Error executing {stmt[:50]}...: {e}")
                
    client.execute("INSERT INTO questions_fts(questions_fts) VALUES('rebuild')")
    
    # Re-insert the rows
    print("Clearing and populating FTS...")
    client.execute("DELETE FROM questions_fts")
    client.execute("""
    INSERT INTO questions_fts (rowid, stem, explanation)
    SELECT q.id, q.stem, e.explanation_text
    FROM questions q
    LEFT JOIN explanations e ON q.id = e.question_id
    """)
    
    print("FTS rebuild complete!")

if __name__ == "__main__":
    rebuild()
