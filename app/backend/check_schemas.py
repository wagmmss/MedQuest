import os, libsql_client
from dotenv import load_dotenv
load_dotenv()
c = libsql_client.create_client_sync(url=os.environ['TURSO_DATABASE_URL'].replace('libsql://', 'https://'), auth_token=os.environ['TURSO_AUTH_TOKEN'])

tables = ['favorites', 'spaced_repetition', 'planner_progress', 'planner_config', 'flashcards']
for table in tables:
    print(table, ":", c.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'").rows)
