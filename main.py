import webview
import os
import sys
import threading
import sqlite3
import json
from agno.agent import Agent
from agno.models.perplexity import Perplexity
from agno.storage.agent.sqlite import SqliteAgentStorage  # Fixed import for Agno/Phidata v2

DB_FILE = "agent_workspace.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('theme', 'light')")
    conn.commit()
    conn.close()

class Api:
    def __init__(self):
        self._api_key = os.environ.get("PERPLEXITY_API_KEY")
        self.window = None
        self.agent_role = "Helpful Assistant"
        self.agent_instructions = "You are a professional assistant. Remember context and be concise."
        # Agno's persistent storage backend
        self.storage = SqliteAgentStorage(table_name="agent_sessions", db_file=DB_FILE)

    def set_window(self, window):
        self.window = window

    def set_api_key(self, key):
        self._api_key = key
        os.environ["PERPLEXITY_API_KEY"] = key
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
        """Loads persistent session history from Agno storage"""
        history = []
        session = self.storage.get_all_sessions()
        if session:
            # We use 'default_session' as our ID
            sess_data = self.storage.read_session("default_session")
            if sess_data and sess_data.memory and sess_data.memory.get('messages'):
                for m in sess_data.memory['messages']:
                    if m['role'] in ['user', 'assistant']:
                        history.append({"role": "bot" if m['role'] == 'assistant' else "user", "content": m['content']})
        return history

    def start_chat_stream(self, user_text, target_id=None):
        if not self._api_key:
            self.window.evaluate_js("receiveError('Please set your Perplexity API Key in Settings.')")
            return
        thread = threading.Thread(target=self._run_agent, args=(user_text, target_id))
        thread.daemon = True
        thread.start()

    def _run_agent(self, user_text, target_id):
        try:
            agent = Agent(
                model=Perplexity(id="sonar-pro", api_key=self._api_key),
                role=self.agent_role,
                instructions=self.agent_instructions,
                storage=self.storage,
                session_id="default_session", # Persistent session ID
                add_history_to_messages=True,
                num_history_runs=5,
                markdown=True
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
    window = webview.create_window("Central 73 | Engineer's Workspace", html_path, js_api=api, width=1200, height=850)
    api.set_window(window)
    webview.start(debug=True)
