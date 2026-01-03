import webview
import os
import sys
import threading
import sqlite3
import json
from datetime import datetime, timezone

from agno.agent import Agent
from agno.models.perplexity import Perplexity
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.text_reader import TextReader
from agno.knowledge.embedder.fastembed import FastEmbedEmbedder
from agno.vectordb.pgvector import PgVector, SearchType
from agno.tools.parallel import ParallelTools
from agno.tools.yfinance import YFinanceTools
from agno.utils.log import logger

# Import db configuration and storage loaders
from db import db_url, load_session_storage, load_personality_storage, load_task_storage

# Load separate storage instances
session_db = load_session_storage()
personality_db = load_personality_storage()
task_db = load_task_storage()

# =========================================================================
# Knowledge Base (optional): PgVector + FastEmbed
# =========================================================================
try:
    agent_knowledge = Knowledge(
        name="Agent Learnings",
        vector_db=PgVector(
            db_url=db_url,
            table_name="agent_learnings",
            search_type=SearchType.hybrid,
            embedder=FastEmbedEmbedder(),
        ),
        max_results=5,
    )
except Exception as e:
    logger.warning(f"[Knowledge] PgVector not available, using SQLite-only fallback: {e}")
    agent_knowledge = None


def init_db():
    # Still use a main workspace DB for app settings and fallback UI history
    workspace_db = "agent_workspace.db"
    conn = sqlite3.connect(workspace_db)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('theme', 'light')")
    conn.commit()
    conn.close()


def _now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# =========================================================================
# Tool: Save Learning
# =========================================================================
def save_learning(
    title: str,
    context: str,
    learning: str,
    confidence: str = "medium",
    type: str = "rule",
) -> str:
    """Save a reusable learning from a successful run."""
    if not title or not title.strip() or not learning or not learning.strip():
        return "Cannot save: title and learning content are required"

    payload = {
        "title": title.strip(),
        "context": context.strip() if context else "",
        "learning": learning.strip(),
        "confidence": confidence,
        "type": type,
        "created_at": _now_z(),
    }

    if agent_knowledge:
        try:
            agent_knowledge.add_content(
                name=payload["title"],
                text_content=json.dumps(payload, ensure_ascii=False),
                reader=TextReader(),
                skip_if_exists=True,
            )
            return f"Learning saved (PgVector): '{payload['title']}'"
        except Exception as e:
            logger.error(f"[Learning] PgVector save failed: {e}")
            return f"Error saving to knowledge base: {e}"
    
    return "Knowledge base not configured. Learning not saved."


class Api:
    def __init__(self):
        self._perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
        self.window = None
        self.agent_role = "Self-Learning Engineering Assistant"
        self.agent_instructions = """You are a Self-Learning Agent that improves over time by capturing and reusing successful patterns.

The loop:
1. Search knowledge base for relevant learnings
2. Gather fresh information (search, APIs)
3. Synthesize answer using both
4. Identify reusable insight
5. Save with user approval

You have dedicated storage for Sessions, Personality Analysis, and Task Extraction."""

    def set_window(self, window):
        self.window = window

    def set_api_key(self, key):
        self._perplexity_key = key
        os.environ["PERPLEXITY_API_KEY"] = key
        return "Perplexity API Key saved"

    def update_agent_config(self, role, instructions):
        self.agent_role = role
        self.agent_instructions = instructions
        return "Config updated"

    def get_theme(self):
        workspace_db = "agent_workspace.db"
        conn = sqlite3.connect(workspace_db)
        res = conn.execute("SELECT value FROM app_settings WHERE key='theme'").fetchone()
        conn.close()
        return res[0] if res else "light"

    def set_theme(self, theme):
        workspace_db = "agent_workspace.db"
        conn = sqlite3.connect(workspace_db)
        conn.execute("UPDATE app_settings SET value=? WHERE key='theme'", (theme,))
        conn.commit()
        conn.close()

    def load_history(self):
        # In Agno v2 with SqliteDb, history is managed by the DB instance
        # For the UI, we could fetch sessions, but returning empty for now as it's handled by Agent memory
        return []

    def start_chat_stream(self, user_text, target_id=None):
        if not self._perplexity_key:
            self.window.evaluate_js("receiveError('Please set your Perplexity API Key in Settings.')")
            return
        thread = threading.Thread(target=self._run_agent, args=(user_text, target_id))
        thread.daemon = True
        thread.start()

    def _run_agent(self, user_text, target_id):
        try:
            # Self-Learning Agent using Perplexity Sonar and persistent SqliteDb
            agent = Agent(
                model=Perplexity(id="sonar-pro", api_key=self._perplexity_key),
                role=self.agent_role,
                instructions=self.agent_instructions,
                db=session_db, # Agno v2 persistent storage
                knowledge=agent_knowledge,
                tools=[ParallelTools(), YFinanceTools(), save_learning],
                search_knowledge=bool(agent_knowledge),
                add_datetime_to_context=True,
                add_history_to_messages=True,
                num_history_responses=5,
                markdown=True,
                session_id="default_perplexity_gui"
            )

            full_response = ""
            run_response = agent.run(user_text, stream=True)

            if target_id:
                self.window.evaluate_js(f"clearBubble('{target_id}')")

            for chunk in run_response:
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if content:
                    full_response += content
                    self.window.evaluate_js(f"receiveChunk({json.dumps(content)}, '{target_id or ''}')")

            self.window.evaluate_js("streamComplete()")
        except Exception as e:
            logger.error(f"Agent error: {e}")
            self.window.evaluate_js(f"receiveError({json.dumps(str(e))})")


if __name__ == '__main__':
    init_db()
    api = Api()
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    html_path = os.path.join(base_path, "ui", "index.html")
    window = webview.create_window(
        "Central 73 | Perplexity Agent with Persistent Storage",
        html_path,
        js_api=api,
        width=1200,
        height=850,
    )
    api.set_window(window)
    webview.start(debug=True)
