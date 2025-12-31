

# General Assistant

A desktop-based AI chat workspace built with **Python + PyWebView** and a modern animated web UI.
Central 73 integrates the **Perplexity (Sonar) model via Agno**, supports **persistent chat memory**, and provides a configurable, engineer-friendly interface with theming, streaming responses, and markdown rendering.

---

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Architecture](#architecture)
* [Requirements](#requirements)
* [Installation](#installation)
* [Configuration](#configuration)
* [Usage](#usage)
* [Persistence & Storage](#persistence--storage)
* [UI Details](#ui-details)
* [Troubleshooting](#troubleshooting)
* [Roadmap](#roadmap)
* [License](#license)

---

## Overview

**Central 73** is an experimental desktop AI assistant workspace designed for engineers and technical users. It uses:

* **PyWebView** to embed a local HTML/JS UI
* **anime.js** for smooth UI animations
* **marked.js** for Markdown rendering
* **Agno (Phidata v2)** for agent orchestration and persistent memory
* **Perplexity Sonar-Pro** as the LLM backend

The app runs locally, stores chat history in SQLite, and streams responses token-by-token to the UI.

---

## Features

* 🖥 Desktop app (no browser required)
* 🤖 Perplexity Sonar-Pro LLM via Agno
* 💾 Persistent chat memory (SQLite)
* ⚡ Streaming responses
* 🧠 Configurable agent role & instructions
* 🌙 Light / Dark mode
* 📝 Markdown rendering
* 🎬 Smooth UI animations (anime.js)
* 📋 Copy & redo responses

---

## Architecture

```
anime.js_experiment/
│
├── main.py                 # Python backend (PyWebView + Agent)
├── agent_workspace.db      # SQLite database (auto-created)
│
└── ui/
    ├── index.html          # Web UI
    ├── anime.min.js        # Animation engine
    └── marked.min.js       # Markdown renderer
```

### Backend

* Python API exposed to JS via `pywebview.api`
* Threaded agent execution to avoid UI blocking
* SQLite-backed persistent memory using Agno’s `SqliteAgentStorage`

### Frontend

* Single-page HTML app
* Streaming updates via JS callbacks
* Animated sidebar & chat bubbles

---

## Requirements

### Python

* Python **3.9+**

### Python Dependencies

```bash
pip install pywebview agno sqlite-utils
```

> You must also have **Perplexity API access**.

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Lmao53and2/anime.js_experiment.git
   cd anime.js_experiment
   ```

2. **Install dependencies**

   ```bash
   pip install pywebview agno
   ```

3. **Run the app**

   ```bash
   python main.py
   ```

---

## Configuration

### Perplexity API Key

You can set the API key in either way:

#### Option 1 — UI (Recommended)

* Open **Settings**
* Paste your API key
* Click **Save Config**

#### Option 2 — Environment Variable

```bash
export PERPLEXITY_API_KEY="your_key_here"
```

---

### Agent Configuration

From the **Settings sidebar** you can configure:

* **Agent Role**

  ```
  Engineering Assistant
  ```
* **Instructions**

  ```
  Be technical and accurate.
  ```

These values are injected directly into the Agno `Agent`.

---

## Usage

1. Launch the app
2. Type a message into the input box
3. Press **Enter** or click **↑**
4. Watch the response stream live
5. Use toolbar options:

   * **Copy** → copy response text
   * **Redo** → regenerate response

Chat history persists across restarts.

---

## Persistence & Storage

Central 73 uses **SQLite** for:

### App Settings

Stored in `app_settings`:

* Theme (`light` / `dark`)

### Chat Memory

* Stored using `SqliteAgentStorage`
* Session ID: `default_session`
* Last 5 runs are injected into context automatically

Database file:

```
agent_workspace.db
```

---

## UI Details

* **Theme system** via CSS variables
* **Animated sidebar** using anime.js
* **Markdown rendering** via marked.js
* **Streaming updates** without full re-render
* **Keyboard-friendly** input

---

## Troubleshooting

### App opens but no responses appear

* Ensure your **Perplexity API key** is set
* Check terminal for Python exceptions

### UI not loading

* Confirm `ui/index.html` exists relative to `main.py`
* If packaged, ensure `_MEIPASS` path is correct

### Database issues

* Delete `agent_workspace.db` to reset app state

---

## Roadmap

Potential future improvements:

* 🔌 Multiple agent profiles
* 🧵 Multiple chat sessions
* 📦 App packaging (PyInstaller)
* 🧠 Tool/function calling
* 📁 File upload & RAG support

---

## License

MIT
