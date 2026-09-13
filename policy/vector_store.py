import os

from dotenv import load_dotenv #type: ignore
from pinecone import Pinecone, ServerlessSpec #type: ignore
from sentence_transformers import SentenceTransformer #type: ignore


load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError(
        "PINECONE_API_KEY is not set in the .env file."
    )


pc = Pinecone(api_key=PINECONE_API_KEY)

INDEX_NAME = "leave-policy"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)


def get_or_create_index():

    existing_indexes = pc.list_indexes().names()

    if INDEX_NAME not in existing_indexes:

        print(f"Creating Pinecone index: {INDEX_NAME}")

        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        print(f"Index '{INDEX_NAME}' created.")

    else:

        print(f"Using existing Pinecone index: {INDEX_NAME}")

    return pc.Index(INDEX_NAME)


def embed_text(text: str):

    vector = embedding_model.encode(
        text,
        normalize_embeddings=True
    )

    return vector.tolist()


def upsert_chunks(chunks):

    index = get_or_create_index()

    vectors = []

    for i, chunk in enumerate(chunks):

        vector = embed_text(chunk["text"])

        metadata = {
    "text": chunk["text"],
    "page": chunk["page"],
    "country": chunk["country"] or "",
    "section": chunk["section"] or "",
    "leave_types": ", ".join(chunk["leave_types"]),
    "is_annual_leave": "Annual Leave" in chunk["leave_types"],
    "is_sick_leave": "Sick Leave" in chunk["leave_types"],
    "is_marriage_leave": "Marriage Leave" in chunk["leave_types"],
    "is_maternity_paternity": "Maternity / Paternity Leaves" in chunk["leave_types"],
    "is_public_holiday": "Official and Public Holidays" in chunk["leave_types"],
    "is_unpaid_leave": "Unpaid Leave" in chunk["leave_types"],
    "is_compassionate_leave": "Compassionate Leave" in chunk["leave_types"],
    "is_hajj_leave": "Hajj Leave" in chunk["leave_types"],
}

        vectors.append({
            "id": f"policy-{i}",
            "values": vector,
            "metadata": metadata
        })

    if vectors:
        index.upsert(vectors=vectors)

    print(
        f"Upserted {len(vectors)} chunks into Pinecone."
    )

    return index