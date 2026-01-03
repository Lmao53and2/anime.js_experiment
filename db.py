import os
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.vectordb.pgvector import PgVector

# Database URL for PostgreSQL (with pgvector extension)
# Format: postgresql://username:password@host:port/database
db_url = os.environ.get("DATABASE_URL", "postgresql://ai:ai@localhost:5432/ai")

# Shared storage for agent sessions
agent_storage = PostgresAgentStorage(table_name="agent_sessions", db_url=db_url)
