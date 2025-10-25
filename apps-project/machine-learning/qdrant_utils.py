import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from embeddings import get_embedding

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

class QdrantHandler:
    @staticmethod
    def create_collection_if_not_exists(collection_name: str):
        """Crea la colección si no existe aún."""
        collections = client.get_collections().collections
        if not any(col.name == collection_name for col in collections):
            client.collection_exists(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
            )
            print(f"✅ Colección '{collection_name}' creada con tamaño 768.")
        else:
            print(f"ℹ️ Colección '{collection_name}' ya existe.")

    @staticmethod
    def upsert_text(collection_name: str, text: str):
        """Inserta o actualiza un texto en una colección."""
        vector = get_embedding(text)
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=abs(hash(text)) % (10**12),
                    vector=vector,
                    payload={"text": text}
                )
            ]
        )
        print(f"✅ Texto agregado/actualizado: {text}")

    @staticmethod
    def bulk_upsert_texts(collection_name: str, texts: list[str]):
        """Inserta múltiples textos en una colección."""
        points = []
        for text in texts:
            vector = get_embedding(text)
            points.append(
                models.PointStruct(
                    id=abs(hash(text)) % (10**12),
                    vector=vector,
                    payload={"text": text}
                )
            )

        client.upsert(collection_name=collection_name, points=points)
        print(f"✅ Se insertaron {len(texts)} textos en '{collection_name}'.")

    @staticmethod
    def get_vectors(collection_name: str, limit: int = 10000):
        """Obtiene todos los vectores de una colección."""
        vectors = []
        next_page = None
        while True:
            result, next_page = client.scroll(
                collection_name=collection_name,
                limit=limit,
                offset=next_page
            )
            for point in result:
                vectors.append(point.vector)
            if not next_page:
                break
        return vectors