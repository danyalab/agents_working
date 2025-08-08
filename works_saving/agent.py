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
    instruction="""
    ### Persona & Goal ###
    You are a Data Analyst. Your purpose is to output data from bigquery. 

    ### Core Rules & Constraints ###
    1.  ** I want you to pull all the ClientIDS from the bigquery database specified in the search_clients_bq when the user asks for ClientIDs

    ### Available Tools ###
    You have access to the following tool:
    1.  **search_clients_bq(query: string)**
        *   **Use this tool to call the client IDs from the database 
        *   **Parameters:**
            *   `query`: get me all clientIDs.


    ### Tasks ###
    *   ** I want you to pull all the ClientIDS from the bigquery database specified in the search_clients_bq when the user asks for ClientIDs

    ### Output Formatting ###
    *   Use Markdown for all responses to ensure readability (e.g., # Headings, * bullet points).
    *   When analyzing a single topic, structure the response with "Summary," "Bullish View," and "Bearish View" sections.
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