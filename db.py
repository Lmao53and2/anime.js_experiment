import os
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.vectordb.pgvector import PgVector

# Database URL for PostgreSQL with pgvector (used only for knowledge base embeddings)
db_url = os.environ.get("DATABASE_URL", "postgresql://ai:ai@localhost:5432/ai")

# Agent session storage using SQLite (simpler, no Postgres required for sessions)
agent_storage = SqliteAgentStorage(table_name="agent_sessions", db_file="agent_workspace.db")
