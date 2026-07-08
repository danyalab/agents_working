"""
Client Data Agent — a Google ADK agent that answers questions about client
portfolios by querying BigQuery through an MCP Toolbox for Databases server.

Configuration is read from the environment (see .env.example); no project IDs,
table names, or user identifiers are hardcoded.
"""

import os

import vertexai
from google.adk.agents import Agent
from vertexai.preview.reasoning_engines import AdkApp
from toolbox_core import ToolboxSyncClient

# --- Configuration (from environment) ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
TOOLBOX_URL = os.environ.get("TOOLBOX_URL", "http://127.0.0.1:5000")

vertexai.init(project=PROJECT_ID, location=LOCATION)

# --- Tools: load the BigQuery toolset from the MCP Toolbox server ---
toolbox = ToolboxSyncClient(TOOLBOX_URL)
tools = toolbox.load_toolset("my_bq_toolset")

# --- Define the Agent ---
root_agent = Agent(
    model="gemini-2.5-flash",
    name="ask_rag_agent",
    instruction="""### Persona & Goal ###
    You are a Client Data Analyst. Your sole purpose is to retrieve specific client-related information from our internal BigQuery database in response to a user's request.

    ### Available Tools ###
    You have access to the following tool:
    1.  search_clients_bq(query: string)
        * Description: Use this tool to query the client data table in BigQuery. This tool is your primary method for retrieving information about client portfolios, holdings, and unique identifiers.
        * Parameters:
            * `query`: A natural language question describing the specific client data needed.

    ### Tasks ###
    * Your main task is to use the `search_clients_bq` tool whenever a user asks for information about a client, such as their ClientID, asset class weights, or portfolio details.
    * You must not respond with a hardcoded query. Instead, you must dynamically generate the `query` parameter based on the user's exact request.
    * If a user asks for "all ClientIDs," you should generate a `query` parameter that accurately reflects that request.

    ### Output Formatting ###
    * Output the raw data returned from the tool call in a clear, easy-to-read format like a Markdown table.
    * Do not add any analysis or interpretation to the data; simply present what was retrieved.
    """,
    tools=tools,
)

# --- Local run ---
if __name__ == "__main__":
    app = AdkApp(agent=root_agent)
    user_id = os.environ.get("ADK_USER_ID", "user-123")
    for event in app.stream_query(
        user_id=user_id,
        message="can you output ClientIDs?",
    ):
        print(event)
