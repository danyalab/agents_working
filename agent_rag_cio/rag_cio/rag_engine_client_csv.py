import os
import pandas as pd
import tempfile
from google import genai
from google.cloud import storage
import vertexai
from google.genai.types import (
    GenerateContentConfig,
    Retrieval,
    Tool,
    VertexRagStore,
)
from vertexai import rag

# === SETUP ===
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "wealthaid-2-18d7")
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
EMBEDDING_MODEL = "publishers/google/models/text-embedding-005"

vertexai.init(project=PROJECT_ID, location=LOCATION)
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# === PREPROCESSING FUNCTION ===
def preprocess_csv_files(input_bucket, output_bucket):
    """Convert CSV files in GCS to text-formatted files uploaded to another GCS path for RAG ingestion."""
    storage_client = storage.Client()

    # Parse bucket info
    input_bucket_name = input_bucket.replace('gs://', '').split('/')[0]
    input_prefix = '/'.join(input_bucket.replace('gs://', '').split('/')[1:])

    output_bucket_name = output_bucket.replace('gs://', '').split('/')[0]
    output_prefix = '/'.join(output_bucket.replace('gs://', '').split('/')[1:])

    input_bucket_obj = storage_client.bucket(input_bucket_name)
    output_bucket_obj = storage_client.bucket(output_bucket_name)

    csv_blobs = [blob for blob in input_bucket_obj.list_blobs(prefix=input_prefix)
                 if blob.name.lower().endswith('.csv')]

    print(f"Found {len(csv_blobs)} CSV file(s) to process.")

    for blob in csv_blobs:
        try:
            print(f"⬇ Downloading & converting: {blob.name}")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                blob.download_to_filename(temp_file.name)
                df = pd.read_csv(temp_file.name)

                text_content = f"Financial Data from {os.path.basename(blob.name)}\n"
                text_content += "=" * 50 + "\n\n"
                text_content += f"Dataset Overview:\n"
                text_content += f"- Total records: {len(df)}\n"
                text_content += f"- Columns: {', '.join(df.columns)}\n\n"
                text_content += "Data Records:\n\n"

                for idx, row in df.head(1000).iterrows():
                    text_content += f"Record {idx + 1}:\n"
                    for col, value in row.items():
                        if pd.notna(value):
                            text_content += f"  {col}: {value}\n"
                    text_content += "\n"

                output_blob_name = f"{output_prefix}{os.path.basename(blob.name).replace('.csv', '_processed.txt')}"
                output_blob = output_bucket_obj.blob(output_blob_name)
                output_blob.upload_from_string(text_content)

                print(f"✅ Processed into: {output_blob_name}")

            os.unlink(temp_file.name)

        except Exception as e:
            print(f"❌ Error processing `{blob.name}`: {e}")

# === MAIN EXECUTION ===
def main():
    INPUT_GCS_BUCKET = "gs://data_for_wealthaid2/tables/"
    PROCESSED_GCS_BUCKET = "gs://data_for_wealthaid2/processed/"

    print("📦 Beginning CSV preprocessing...")
    preprocess_csv_files(INPUT_GCS_BUCKET, PROCESSED_GCS_BUCKET)
    print("✅ Preprocessing complete.\n")

    print("🧠 Creating RAG corpus...")
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
    print(f"✅ RAG corpus created: {rag_corpus.name}")

    print("📤 Importing processed files to RAG...")
    rag.import_files(
        corpus_name=rag_corpus.name,
        paths=[PROCESSED_GCS_BUCKET],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=1024, chunk_overlap=100)
        ),
        max_embedding_requests_per_min=900,
    )
    print("✅ Files imported and chunked.\n")

    print("⚙️ Setting up retrieval tool...")
    rag_retrieval_tool = Tool(
        retrieval=Retrieval(
            vertex_rag_store=VertexRagStore(
                rag_corpora=[rag_corpus.name],
                similarity_top_k=10,
                vector_distance_threshold=0.5,
            )
        )
    )

    # Example user question
    question = "What are the names of our clients in our customer_profile dataset?"

    print(f"💬 Asking Gemini: {question}")
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=question,
        config=GenerateContentConfig(tools=[rag_retrieval_tool]),
    )

    print("\n🧾 Gemini Response:\n")
    print(response.text)

if __name__ == "__main__":
    main()
