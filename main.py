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

# Import db configuration (no agno.storage imports here)
from db import db_url, AGENT_DB_FILE

DB_FILE = AGENT_DB_FILE

# =========================================================================
# Knowledge Base (optional): PgVector + FastEmbed
# =========================================================================
# If PgVector dependencies or DATABASE_URL are not configured, the app still runs.
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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # App settings
    c.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('theme', 'light')")

    # Simple persistent chat history (UI + lightweight prompt-memory)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # SQLite fallback learnings (when PgVector isn't available)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            context TEXT,
            learning TEXT NOT NULL,
            confidence TEXT,
            type TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def _now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _insert_chat(role: str, content: str):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO chat_messages(role, content, created_at) VALUES (?, ?, ?)",
        (role, content, _now_z()),
    )
    conn.commit()
    conn.close()


def _get_recent_chat(limit: int = 12):
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT role, content FROM chat_messages ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return list(reversed(rows))


def _search_sqlite_learnings(query: str, limit: int = 5):
    # Very lightweight fallback: keyword LIKE search
    q = f"%{query}%"
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        """
        SELECT title, context, learning, confidence, type, created_at
        FROM learnings
        WHERE title LIKE ? OR context LIKE ? OR learning LIKE ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (q, q, q, limit),
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append(
            {
                "title": r[0],
                "context": r[1] or "",
                "learning": r[2],
                "confidence": r[3] or "medium",
                "type": r[4] or "rule",
                "created_at": r[5],
            }
        )
    return results


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
    """Save a reusable learning from a successful run.

    Uses PgVector when available, otherwise falls back to SQLite.
    """
    if not title or not title.strip():
        return "Cannot save: title is required"
    if not learning or not learning.strip():
        return "Cannot save: learning content is required"
    if len(learning.strip()) < 20:
        return "Cannot save: learning is too short to be useful. Be more specific."

    payload = {
        "title": title.strip(),
        "context": context.strip() if context else "",
        "learning": learning.strip(),
        "confidence": confidence,
        "type": type,
        "created_at": _now_z(),
    }

    # Preferred: PgVector KB
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
            logger.error(f"[Learning] PgVector save failed, falling back to SQLite: {e}")

    # Fallback: SQLite
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        INSERT INTO learnings(title, context, learning, confidence, type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload["title"],
            payload["context"],
            payload["learning"],
            payload["confidence"],
            payload["type"],
            payload["created_at"],
        ),
    )
    conn.commit()
    conn.close()
    return f"Learning saved (SQLite): '{payload['title']}'"


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

Rules:
- Always search learnings first.
- Never call save_learning without explicit user approval.
- When proposing a learning, end with a Proposed Learning block and ask: Save this? (yes/no)
"""

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
        conn = sqlite3.connect(DB_FILE)
        res = conn.execute("SELECT value FROM app_settings WHERE key='theme'").fetchone()
        conn.close()
        return res[0] if res else "light"

    def set_theme(self, theme):
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE app_settings SET value=? WHERE key='theme'", (theme,))
        conn.commit()
        conn.close()

    def load_history(self):
        # UI expects: [{role: 'user'|'bot', content: '...'}]
        msgs = _get_recent_chat(limit=100)
        out = []
        for role, content in msgs:
            out.append({"role": "bot" if role == "assistant" else role, "content": content})
        return out

    def start_chat_stream(self, user_text, target_id=None):
        if not self._perplexity_key:
            self.window.evaluate_js("receiveError('Please set your Perplexity API Key in Settings.')")
            return
        _insert_chat("user", user_text)
        thread = threading.Thread(target=self._run_agent, args=(user_text, target_id))
        thread.daemon = True
        thread.start()

    def _build_prompt_with_memory(self, user_text: str) -> str:
        # Lightweight memory: include recent chat + relevant SQLite learnings.
        recent = _get_recent_chat(limit=12)
        learnings = _search_sqlite_learnings(user_text, limit=5) if not agent_knowledge else []

        parts = []
        if recent:
            parts.append("Recent conversation:\n" + "\n".join([
                ("User: " if r == "user" else "Assistant: ") + c for r, c in recent
            ]))

        if learnings:
            parts.append("Relevant prior learnings (SQLite fallback):\n" + "\n".join([
                f"- {l['title']}: {l['learning']}" for l in learnings
            ]))

        parts.append("User request:\n" + user_text)
        return "\n\n".join(parts)

    def _run_agent(self, user_text, target_id):
        try:
            # Build tools list
            tools = [ParallelTools(), YFinanceTools(), save_learning]

            # If PgVector KB is available, let Agno search it; otherwise prompt contains SQLite learnings.
            final_input = user_text
            if not agent_knowledge:
                final_input = self._build_prompt_with_memory(user_text)

            agent = Agent(
                model=Perplexity(id="sonar-pro", api_key=self._perplexity_key),
                role=self.agent_role,
                instructions=self.agent_instructions,
                knowledge=agent_knowledge,
                tools=tools,
                search_knowledge=bool(agent_knowledge),
                add_datetime_to_context=True,
                markdown=True,
            )

            full_response = ""
            run_response = agent.run(final_input, stream=True)

            if target_id:
                self.window.evaluate_js(f"clearBubble('{target_id}')")

            for chunk in run_response:
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if content:
                    full_response += content
                    self.window.evaluate_js(f"receiveChunk({json.dumps(content)}, '{target_id or ''}')")

            _insert_chat("assistant", full_response)
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
        "Central 73 | Perplexity Learning Agent",
        html_path,
        js_api=api,
        width=1200,
        height=850,
    )
    api.set_window(window)
    webview.start(debug=True)
