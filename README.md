
# Central 73: Self-Learning Agent Workspace

A desktop-based AI chat workspace built with **Python + PyWebView** that implements a **Self-Learning Loop**.
Central 73 integrates **Gemini 3 Flash** and **Perplexity (Sonar)** via **Agno**, supporting continuous system-level learning without fine-tuning.

---

## 🧠 Self-Learning Architecture

The agent follows a "GPU Poor Continuous Learning" loop:
1.  **Search**: Queries a **PgVector** knowledge base for relevant prior learnings.
2.  **Research**: Gathers fresh information using **Perplexity (Sonar)**, **YFinance**, and web search.
3.  **Synthesize**: Combines prior insights with new data.
4.  **Reflect**: Identifies reusable patterns or rules.
5.  **Learn**: Saves insights back to the knowledge base with user approval.

---

## Features

*   🤖 **Gemini 3 Flash** as the primary reasoning engine.
*   🔍 **Sonar-Pro (Perplexity)** integrated for real-time research.
*   📚 **Continuous Learning**: A `save_learning` tool stores insights in a persistent vector database.
*   ⚡ **FastEmbed**: Local high-performance embeddings for the knowledge base.
*   💾 **Persistent Memory**: PostgreSQL-backed session storage.
*   🖥 **Desktop App**: PyWebView interface with smooth anime.js animations.

---

## Requirements

### Prerequisites
*   **PostgreSQL** with the `pgvector` extension.
*   **Google AI (Gemini)** API Key.
*   **Perplexity** API Key.

### Python Dependencies
```bash
pip install -r requirements.txt
```

---

## Configuration

### Database
Update `db.py` with your PostgreSQL connection string:
```python
db_url = "postgresql://user:pass@host:port/dbname"
```

### API Keys
Set your keys in the **Settings** sidebar within the app:
*   **Google API Key**: Required for the Gemini reasoning model.
*   **Perplexity API Key**: Used for research tools.

---

## Usage

1.  Launch the app: `python main.py`.
2.  Interact with the agent.
3.  If the agent identifies a reusable insight, it will propose a "Learning".
4.  Type "yes" or "no" to approve/decline saving the insight to the long-term knowledge base.

---

## Architecture

```
anime.js_experiment/
│
├── main.py                 # PyWebView + Agno Self-Learning Agent
├── db.py                   # Database configuration (PgVector + Postgres)
├── requirements.txt        # Project dependencies
│
└── ui/
    ├── index.html          # Modern Web UI
    ├── anime.min.js        # Animation engine
    └── marked.min.js       # Markdown renderer
```

---

## License
MIT
