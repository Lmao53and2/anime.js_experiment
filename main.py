import webview
import os
import sys
import threading
import sqlite3
import json
from datetime import datetime, timezone

from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.perplexity import Perplexity
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.text_reader import TextReader
from agno.knowledge.embedder.fastembed import FastEmbedEmbedder
from agno.vectordb.pgvector import PgVector, SearchType
from agno.tools.parallel import ParallelTools
from agno.tools.yfinance import YFinanceTools
from agno.utils.log import logger

# Import db configuration
from db import db_url, gemini_agents_db

DB_FILE = "agent_workspace.db"

# ============================================================================
# Knowledge Base: stores successful learnings with FastEmbed
# ============================================================================
agent_knowledge = Knowledge(
    name="Agent Learnings",
    vector_db=PgVector(
        db_url=db_url,
        table_name="agent_learnings",
        search_type=SearchType.hybrid,
        embedder=FastEmbedEmbedder(), # Satisfies fastembedded requirement
    ),
    max_results=5,
    contents_db=gemini_agents_db,
)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('theme', 'light')")
    conn.commit()
    conn.close()

# ============================================================================
# Tool: Save Learning
# ============================================================================
def save_learning(
    title: str,
    context: str,
    learning: str,
    confidence: str = "medium",
    type: str = "rule",
) -> str:
    """
    Save a reusable learning from a successful run.
    """
    if not title or not title.strip() or not learning or not learning.strip():
        return "Cannot save: title and learning content are required"
    
    payload = {
        "title": title.strip(),
        "context": context.strip() if context else "",
        "learning": learning.strip(),
        "confidence": confidence,
        "type": type,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    try:
        agent_knowledge.add_content(
            name=payload["title"],
            text_content=json.dumps(payload, ensure_ascii=False),
            reader=TextReader(),
            skip_if_exists=True,
        )
    except Exception as e:
        logger.error(f"[Learning] Failed to save: {e}")
        return f"Failed to save learning: {e}"

    logger.info(f"[Learning] Saved: {payload['title']}")
    return f"Learning saved: '{payload['title']}'"

class Api:
    def __init__(self):
        self._perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
        self._google_key = os.environ.get("GOOGLE_API_KEY")
        self.window = None
        self.agent_role = "Self-Learning Engineering Assistant"
        self.agent_instructions = """You are a Self-Learning Agent that improves over time by capturing and reusing successful patterns.
You build institutional memory: successful insights get saved to a knowledge base.

## Workflow
1. SEARCH KNOWLEDGE FIRST — Call `search_knowledge` before anything else.
2. RESEARCH — Use `parallel_search`, `yfinance`, or search tools to gather fresh information.
3. SYNTHESIZE — Combine prior learnings with new info.
4. REFLECT — Consider if this task revealed a reusable insight.
5. PROPOSE — If worth saving, end response with 'Proposed Learning' block."""

    def set_window(self, window):
        self.window = window

    def set_api_key(self, key):
        # We assume Perplexity key for now, or handle both
        if key.startswith("pplx-"):
            self._perplexity_key = key
            os.environ["PERPLEXITY_API_KEY"] = key
        else:
            self._google_key = key
            os.environ["GOOGLE_API_KEY"] = key
        return "Key saved"

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
        # Implementation to load from gemini_agents_db
        history = []
        try:
            # Simplified for UI display
            pass
        except:
            pass
        return history

    def start_chat_stream(self, user_text, target_id=None):
        if not self._google_key:
            self.window.evaluate_js("receiveError('Please set your Google API Key (for Gemini) in Settings.')")
            return
        thread = threading.Thread(target=self._run_agent, args=(user_text, target_id))
        thread.daemon = True
        thread.start()

    def _run_agent(self, user_text, target_id):
        try:
            # Self-Learning Agent using Gemini 3 Flash
            agent = Agent(
                model=Gemini(id="gemini-3-flash-preview", api_key=self._google_key),
                role=self.agent_role,
                instructions=self.agent_instructions,
                db=gemini_agents_db,
                knowledge=agent_knowledge,
                tools=[
                    ParallelTools(),
                    YFinanceTools(),
                    # Perplexity used as a tool for research (Sonar requirement)
                    Agent(model=Perplexity(id="sonar-pro"), name="Sonar Search", tools=[ParallelTools()]),
                    save_learning,
                ],
                enable_agentic_memory=True,
                search_knowledge=True,
                add_datetime_to_context=True,
                add_history_to_context=True,
                num_history_runs=5,
                markdown=True,
                session_id="default_gui_session"
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
            self.window.evaluate_js(f"receiveError({json.dumps(str(e))})")

if __name__ == '__main__':
    init_db()
    api = Api()
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    html_path = os.path.join(base_path, "ui", "index.html")
    window = webview.create_window("Central 73 | Self-Learning Agent", html_path, js_api=api, width=1200, height=850)
    api.set_window(window)
    webview.start(debug=True)
