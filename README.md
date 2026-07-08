# Wealth-Management Agents (Google ADK + Vertex AI)

Two **Google Agent Development Kit (ADK)** agents that answer wealth-management questions by combining structured data (BigQuery) with unstructured research (a Vertex AI RAG corpus of "CIO views"). Built on Gemini 2.5 Flash, with the BigQuery tool served through an **MCP Toolbox for Databases** server.

| Agent | Tools | What it does |
|-------|-------|--------------|
| **`client_data_agent`** | BigQuery (via MCP Toolbox) | Answers questions about client portfolios, holdings, and identifiers by generating SQL against a client-data table on demand. |
| **`cio_rag_agent`** | BigQuery **+** Vertex AI RAG retrieval | Combines the client-data tool with retrieval over an internal "CIO views" knowledge base to give balanced, disclaimer-first market and allocation analysis — and can cross-reference a client's holdings against the house view. |

```
                     ┌──────────────────────────┐
     user question ─►│   ADK Agent (Gemini)     │
                     └────────────┬─────────────┘
                    ┌─────────────┴──────────────┐
                    ▼                            ▼
          ┌───────────────────┐        ┌──────────────────────┐
          │  MCP Toolbox svr  │        │  Vertex AI RAG        │
          │  → BigQuery SQL   │        │  → "CIO views" corpus │
          └───────────────────┘        └──────────────────────┘
             (client data)                (research / house view)
```

---

## How it works

- **Agents as tool-routers.** Each agent is a Gemini model given a persona, strict tool-adherence rules, and one or two tools. The `cio_rag_agent`'s prompt enforces a compliance disclaimer on the first turn, requires balanced bull/bear views, defaults to a three-month lookback, and routes client questions to BigQuery vs. market questions to RAG.
- **BigQuery access via MCP.** Rather than embedding SQL in the agent, a [MCP Toolbox for Databases](https://github.com/googleapis/genai-toolbox) server exposes a `search_clients_bq` tool (defined declaratively in `mcp-toolbox/tools.yaml`). The agent loads that toolset over MCP and generates natural-language queries the tool translates to SQL.
- **RAG retrieval.** `cio_rag_agent` attaches a `VertexAiRagRetrieval` tool over a Vertex AI RAG corpus (top-k = 10, distance threshold 0.6) so answers are grounded in retrieved research, not the model's parametric knowledge.

See `guides/register-adk-agent-to-agentspace.md` for how to register a deployed ADK reasoning engine with Agentspace, and `samples/cio_views_sample.md` for an example of the RAG agent's output.

---

## Configuration

Everything environment-specific is read from env vars — nothing is hardcoded. Copy the template and fill in your own values:

```bash
cp .env.example .env
```

| Variable | Meaning |
|----------|---------|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `GOOGLE_CLOUD_REGION` | Vertex AI / BigQuery region (default `us-central1`) |
| `RAG_CORPUS_ID` | Numeric id of your Vertex AI RAG corpus (used by `cio_rag_agent`) |
| `TOOLBOX_URL` | URL of your running MCP Toolbox server (default `http://127.0.0.1:5000`) |
| `ADK_USER_ID` | User id passed to `stream_query` for local runs |

Also edit `mcp-toolbox/tools.yaml` to point `project` and the `FROM` table at your own BigQuery dataset.

---

## Run it

Prerequisites: a GCP project with Vertex AI + BigQuery enabled, a populated RAG corpus (for the CIO agent), and the [MCP Toolbox server](https://github.com/googleapis/genai-toolbox) running against your BigQuery.

```bash
pip install -r requirements.txt

# In one terminal: start the MCP Toolbox server with your tools.yaml
# ./toolbox --tools-file mcp-toolbox/tools.yaml

# In another: run an agent locally
python client_data_agent/agent.py
python cio_rag_agent/agent.py
```

---

## Notes

- This is a **demo / learning project** exploring the ADK + Vertex RAG + MCP-Toolbox pattern; it expects synthetic sample data, not real client records.
- No credentials, project IDs, corpus IDs, or client data are committed — all such values are placeholders supplied via `.env` / `tools.yaml`.

## Tech

Google Agent Development Kit (ADK) · Vertex AI (Gemini 2.5 Flash, RAG corpora, Reasoning Engine / `AdkApp`) · MCP Toolbox for Databases · BigQuery.
