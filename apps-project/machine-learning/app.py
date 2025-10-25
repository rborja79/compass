import os
import logging
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel
from embeddings import get_embedding
from clustering import create_clusters, calculate_centroids, save_centroids, suggest_n_clusters

# ==========================
# 📝 LOGGING CONFIG
# ==========================
logger = logging.getLogger("MLLogger")
logger.setLevel(logging.INFO)

# ==========================
# 🔐 Seguridad básica por API KEY
# ==========================
API_KEY = os.getenv("ML_API_KEY", "")

app = FastAPI(title="ML Tools", version="1.0")

# 📥 Modelo de request
class TextRequest(BaseModel):
    text: str

class ClusterRequest(BaseModel):
    collection: str
    n_clusters: int = 5

class SuggestRequest(BaseModel):
    collection: str
    k_min: int = 2
    k_max: int = 15

class SaveRequest(BaseModel):
    collection: str

# ==========================
# 🔐 Verificación de API Key
# ==========================
def verify_api_key(x_api_key: str | None):
    if not API_KEY:
        return
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# ==========================
# 🩺 Health check
# ==========================
@app.get("/health")
def health():
    return {"status": "ok"}


# 🧠 Endpoint para generar embeddings
@app.post("/embed")
async def embed_endpoint(req: TextRequest):
    """
    Genera el embedding de un texto usando el modelo configurado.
    """
    vector = get_embedding(req.text)
    return {"embedding": vector}


# 🧠 Endpoint para clustering
@app.post("/clusters/create")
def create(req: ClusterRequest, x_api_key: str | None = Header(default=None)):
    verify_api_key(x_api_key)
    create_clusters(req.collection, req.n_clusters)
    return {"message": f"Clusters creados para {req.collection}"}


@app.post("/centroids/calculate")
def calc(req: ClusterRequest, x_api_key: str | None = Header(default=None)):
    verify_api_key(x_api_key)
    centroids = calculate_centroids(req.collection)
    return {"collection": req.collection, "centroids": centroids}


@app.post("/centroids/save")
def save(req: SaveRequest):
    # Paso 1: Calcular centroides
    centroids = calculate_centroids(req.collection)
    if not centroids:
        logger.warning(f"No se encontraron centroides para la colección {req.collection}")
        return {"message": "No se generaron centroides."}

    # Paso 2: Guardarlos
    save_centroids(req.collection, centroids)
    return {"message": f"{len(centroids)} centroides guardados en {req.collection}_centroids"}


@app.post("/clusters/suggest")
def suggest(req: SuggestRequest, x_api_key: str | None = Header(default=None)):
    verify_api_key(x_api_key)
    result = suggest_n_clusters(req.collection, req.k_min, req.k_max)
    return result