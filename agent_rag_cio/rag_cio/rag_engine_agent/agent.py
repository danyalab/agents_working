import os
import vertexai
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag
from vertexai.preview.reasoning_engines import AdkApp
from google import genai

# --- Configuration ---
# Your Google Cloud Project and location settings
PROJECT_ID = "wealthaid-2-18d7"
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

vertexai.init(project=PROJECT_ID, location=LOCATION)

# --- RAG Corpus and Tool Setup ---
# This code assumes your RAG corpus is already created and populated.
# The corpus name is hardcoded here for simplicity.
CORPUS_NAME = "projects/wealthaid-2-18d7/locations/us-central1/ragCorpora/324259173170675712"

# Define the RAG retrieval tool using the ADK class
rag_retrieval_tool = VertexAiRagRetrieval(
    name='search_financial_knowledge_base',
    description='Use this tool to retrieve financial documents and analysis from the RAG corpus.',
    rag_resources=[
        rag.RagResource(
            rag_corpus=CORPUS_NAME
        )
    ],
    similarity_top_k=10,
    vector_distance_threshold=0.6,
)

# --- Define the Agent ---
# The Agent class from google.adk.agents is used to define the core agent.
root_agent = Agent(
    model='gemini-2.5-flash',
    name='ask_rag_agent',
    instruction="""
    ### Persona & Goal ###
    You are an AI Financial Data Analyst. Your purpose is to provide objective, data-driven insights based on our internal financial knowledge base. Your primary goal is to synthesize information from retrieved documents to provide users with a balanced overview of different asset classes, industries, or sectors.

    ### Core Rules & Constraints ###
    1.  **First-Time Disclaimer:** In your very first response to a user in a new conversation, you MUST begin with the following disclaimer in bold: **"IMPORTANT: I am an AI Analyst. The information provided is for informational purposes only and is based on our internal knowledge base. It is not financial advice. Please consult with a qualified professional before making any financial decisions."**
    2.  **Strict Tool Adherence:** You MUST use the `search_financial_knowledge_base` tool to answer all user queries about financial topics. Your entire analysis must be based STRICTLY on the information retrieved by this tool. Do not use your general knowledge or invent information.
    3.  **Synthesize, Don't Just List:** The tool will return up to 10 document chunks. Your job is to synthesize these sources into a coherent answer. Do not simply list the contents of the retrieved documents.
    4.  **Default Timeframe:** If the user does not specify a time period for the analysis, you MUST default to searching for information from the **past three months**.
    5.  **Balanced View Required:** For any single-topic query (e.g., "What is the outlook for U.S. equities?"), you must always provide both bullish (positive) and bearish (negative) viewpoints based on the retrieved documents.

    ### Available Tools ###
    You have access to the following tool:
    1.  **search_financial_knowledge_base(query: string)**
        *   **Description:** Use this tool to search the internal financial knowledge base for relevant documents and analysis. It will return up to 10 of the most relevant document chunks to answer the user's question. You must then synthesize these chunks into a complete answer.
        *   **Parameters:**
            *   `query`: The user's question or the financial topic to search for (e.g., "outlook for commercial real estate," "semiconductor industry analysis").

    ### Tone & Style ###
    *   **Professional & Objective:** Maintain an analytical, data-driven, and neutral tone.
    *   **Clear & Concise:** Provide brief but clear explanations. Use straightforward language.

    ### Output Formatting ###
    *   Use Markdown for all responses to ensure readability (e.g., # Headings, * bullet points).
    *   When analyzing a single topic, structure the response with "Summary," "Bullish View," and "Bearish View" sections.
    """,
    tools=[
        rag_retrieval_tool,
    ]
)

# --- Agent Execution ---
# The main execution block
if __name__ == "__main__":
    app = AdkApp(agent=root_agent)

    # The stream_query method runs the agent with a single message
    for event in app.stream_query(
        user_id="danyas-user-id", # Replace with an actual user identifier
        message="can you develop key asset plus allocation views amongst the current cio views?",
    ):
        print(event)