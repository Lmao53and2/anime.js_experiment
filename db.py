import os

# Optional: PostgreSQL URL for PgVector knowledge base (if configured)
db_url = os.environ.get("DATABASE_URL", "postgresql://ai:ai@localhost:5432/ai")

# Local SQLite file used by the desktop app for settings + chat history
AGENT_DB_FILE = os.environ.get("AGENT_DB_FILE", "agent_workspace.db")

# Agno storage is intentionally NOT imported here because some agno PyPI builds
# do not ship the storage subpackage. The app will run without it.
agent_storage = None
