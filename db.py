import os
from agno.storage.sqlite import SqliteStorage

# Database URL for PostgreSQL with pgvector (optional - for knowledge base embeddings)
db_url = os.environ.get("DATABASE_URL", "postgresql://ai:ai@localhost:5432/ai")

# Agent session storage using SQLite
agent_storage = SqliteStorage(
    table_name="agent_sessions",
    db_file="agent_workspace.db"
)
