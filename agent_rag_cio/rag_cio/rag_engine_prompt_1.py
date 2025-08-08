import os
from google.genai.types import (
    GenerateContentConfig,
    Retrieval,
    Tool,
    VertexRagStore,
)
from vertexai import rag
from google import genai
import vertexai


PROJECT_ID = "wealthaid-2-18d7"  # @param {type: "string", placeholder: "[your-project-id]", isTemplate: true}
if not PROJECT_ID or PROJECT_ID == "[your-project-id]":
    PROJECT_ID = str(os.environ.get("GOOGLE_CLOUD_PROJECT"))

LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

vertexai.init(project=PROJECT_ID, location=LOCATION)
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# Currently supports Google first-party embedding models
EMBEDDING_MODEL = "publishers/google/models/text-embedding-005"  # @param {type:"string", isTemplate: true}

rag_corpus = rag.create_corpus(
    display_name="my-rag-corpus",
    backend_config=rag.RagVectorDbConfig(
        rag_embedding_model_config=rag.RagEmbeddingModelConfig(
            vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                publisher_model=EMBEDDING_MODEL
            )
        )
    ),
)

corpora = rag.list_corpora()
#print(corpora)

rag_file = rag.upload_file(
    corpus_name=rag_corpus.name,
    path="test.md",
    display_name="test.md",
    description="my test file",
)

INPUT_GCS_BUCKET = (
    "gs://downloaded_pdfs/downloaded_pdfs"
)

response = rag.import_files(
    corpus_name=rag_corpus.name,
    paths=[INPUT_GCS_BUCKET],
    # Optional
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=1024, chunk_overlap=100)
    ),
    max_embedding_requests_per_min=900,  # Optional
)

corpus_name=rag_corpus.name
# List files (documents) in the corpus:
files = rag.list_files(corpus_name=corpus_name)

# Create a tool for the RAG Corpus
rag_retrieval_tool = Tool(
    retrieval=Retrieval(
        vertex_rag_store=VertexRagStore(
            rag_corpora=[rag_corpus.name],
            similarity_top_k=10,
            vector_distance_threshold=0.5,
        )
    )
)

# (Assume you have: `new_idea = "...user's query..."`)
analyst_prompt = """
You are a meticulous strategic analyst. Your task is to analyze a user's New Idea in the context of several Retrieved Documents provided from a knowledge base. You must compare the New Idea against the core concepts contained within each document.
The Retrieved Documents are raw text chunks and may not have structured metadata. Your first step is to process them.

Your Instructions
Process Each Document: For each Retrieved Document, perform the following pre-analysis:
Summarize the Core Idea: Read the document and write a concise, one-sentence summary of the main idea, proposal, or finding it contains.
Infer the Source/Date: Carefully examine the text for any mention of a date, timeline, project name, or source (e.g., "from the Q3 planning session," "in the 2023-01-15 memo," "according to the Phoenix Project brief"). Record this as the source. If no specific source or date can be found, state "Source Document [N]" where N is the document number.
Conduct the Analysis: Once you have processed all documents, compare the user's New Idea against the summarized core idea of each retrieved document.
Identify any conceptual overlaps, shared goals, or thematic similarities. If there are none, you must explicitly state "None."
Identify any direct contradictions, strategic differences, or contrasting points. If there are none, you must explicitly state "None."
Format the Output: Present your complete analysis only as a single Markdown table. Do not include any introductory or concluding text. The table must have the following columns, in this exact order:
Inferred Date / Source | Previous Idea Summary | Overlaps with New Idea | Contrasts with New Idea
"""


MODEL_ID = "gemini-2.0-flash-001"
new_idea = "We should build an automated onboarding wizard for new SMB customers."  # replace with your idea

# The prompt must contain your system prompt, a clear “New Idea” section, and let the tool do the Retrieval
model_prompt = f"""{analyst_prompt}

New Idea:
{new_idea}

Retrieved Documents:
(The RAG tool will supply these automatically.)"""

response = client.models.generate_content(
    model=MODEL_ID,
    contents=model_prompt,
    config=GenerateContentConfig(tools=[rag_retrieval_tool]),
)
print(response.text)


# Optional: The retrieved context can be passed to any SDK or model generation API to generate final results.
# context = " ".join([context.text for context in response.contexts.contexts]).replace("\n", "")