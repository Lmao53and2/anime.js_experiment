
# Central 73: Perplexity Self-Learning Agent

A desktop-based AI chat workspace built with **Python + PyWebView** that implements a **Self-Learning Loop** powered exclusively by **Perplexity API**.
Central 73 uses **Sonar-Pro** via **Agno** to gather real-time data and build a long-term institutional memory.

---

## 🧠 Self-Learning Architecture

The agent follows a "GPU Poor Continuous Learning" loop without fine-tuning:
1.  **Search**: Queries a **PgVector** knowledge base for relevant prior learnings using local **FastEmbed** embeddings.
2.  **Research**: Gathers fresh information using **Perplexity (Sonar)** and **YFinance**.
3.  **Synthesize**: Merges historical patterns with fresh search data.
4.  **Reflect**: Identifies reusable patterns or rules from the current task.
5.  **Learn**: Saves insights back to the knowledge base with user approval.

---

## Features

*   🤖 **Perplexity Sonar-Pro** as the primary reasoning and search engine.
*   🔍 **Built-in Research**: Native integration with Perplexity for up-to-the-minute information.
*   📚 **Continuous Learning**: A `save_learning` tool stores insights in a persistent vector database.
*   ⚡ **FastEmbed**: High-performance local embeddings to keep the "GPU Poor" requirement.
*   💾 **Persistent Memory**: PostgreSQL-backed session storage via Agno.
*   🖥 **Desktop App**: PyWebView interface with smooth anime.js animations.

---

## Requirements

### Prerequisites
*   **PostgreSQL** with the `pgvector` extension.
*   **Perplexity API Key**.

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
*   **Perplexity API Key**: Required for both reasoning and research.

---

## Usage

1.  Launch the app: `python main.py`.
2.  Interact with the agent. The agent will automatically use Perplexity to research complex queries.
3.  If a reusable insight is identified, approve the "Proposed Learning" to save it to long-term memory.

---

## Architecture

```
anime.js_experiment/
│
├── main.py                 # PyWebView + Agno Perplexity Agent
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
