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

MODEL_ID = "gemini-2.0-flash-001"
response = client.models.generate_content(
    model=MODEL_ID,
    contents="can you develop key asset plus allocation views amongst the current cio views?",
    config=GenerateContentConfig(tools=[rag_retrieval_tool]),
)

print(response.text)

# Optional: The retrieved context can be passed to any SDK or model generation API to generate final results.
# context = " ".join([context.text for context in response.contexts.contexts]).replace("\n", "")