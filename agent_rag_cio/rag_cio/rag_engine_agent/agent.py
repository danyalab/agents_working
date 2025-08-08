import os
import vertexai
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag
from vertexai.preview.reasoning_engines import AdkApp
from google import genai
from toolbox_core import ToolboxSyncClient

toolbox = ToolboxSyncClient("http://127.0.0.1:5000")
tools = toolbox.load_toolset('my_bq_toolset')

# --- Configuration ---
# Your Google Cloud Project and location settings
PROJECT_ID = "wealthaid-2-18d7"
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

vertexai.init(project=PROJECT_ID, location=LOCATION)


# --- Define the Agent ---
# The Agent class from google.adk.agents is used to define the core agent.
root_agent = Agent(
    model='gemini-2.5-flash',
    name='ask_rag_agent',
    instruction=
    """### Persona & Goal ###
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

# --- Agent Execution ---
# The main execution block
if __name__ == "__main__":
    app = AdkApp(agent=root_agent)

    # The stream_query method runs the agent with a single message
    for event in app.stream_query(
        user_id="danyas-user-id", # Replace with an actual user identifier
        message="can you output ClientIDs?",
    ):
        print(event)