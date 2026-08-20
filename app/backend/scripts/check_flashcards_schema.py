import os, libsql_client
from dotenv import load_dotenv
load_dotenv()
c = libsql_client.create_client_sync(url=os.environ['TURSO_DATABASE_URL'].replace('libsql://', 'https://'), auth_token=os.environ['TURSO_AUTH_TOKEN'])
print(c.execute("SELECT sql FROM sqlite_master WHERE name='flashcards'").rows)
