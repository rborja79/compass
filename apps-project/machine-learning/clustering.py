import logging
import os
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.cluster import KMeans
from qdrant_client import QdrantClient
from qdrant_client.http import models

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# ==========================
# 📜 Configuración del logger
# ==========================
logger = logging.getLogger("ClusteringLogger")
logger.setLevel(logging.DEBUG)  # Usa INFO en prod si no quieres tanto ruido
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def _normalize_vector(vec: Any) -> List[float]:
    """
    Qdrant puede devolver vector como lista o como dict {"default": [...] }.
    Esta función lo estandariza a una lista de floats.
    """
    if vec is None:
        return []
    if isinstance(vec, dict):
        # si tienes múltiples nombres de vector, ajusta aquí
        vec = vec.get("default", [])
    return list(vec)


def get_points_from_collection(
    collection_name: str,
    with_payload: bool = False,
    batch_size: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Devuelve SIEMPRE una lista de dicts: {"id": id, "vector": [...], "payload": {...}}
    """
    out: List[Dict[str, Any]] = []
    next_page = None

    while True:
        res, next_page = client.scroll(
            collection_name=collection_name,
            with_vectors=True,
            with_payload=with_payload,
            limit=batch_size,
            offset=next_page,
        )
        for p in res:
            vec = _normalize_vector(getattr(p, "vector", None))
            payload = getattr(p, "payload", None) or {}
            out.append({"id": p.id, "vector": vec, "payload": payload})
        if next_page is None:
            break

    return out


def create_clusters(collection_name: str, n_clusters: int = 5) -> Dict[str, Any]:
    """
    Entrena KMeans sobre los vectores y asigna cluster_id a cada punto (payload).
    No guarda centroides; solo etiqueta puntos.
    """
    points = get_points_from_collection(collection_name, with_payload=False)
    if not points:
        return {"collection": collection_name, "n_clusters": 0, "counts": []}

    vectors = np.array([p["vector"] for p in points], dtype=float)
    ids = [p["id"] for p in points]

    if len(vectors) < n_clusters:
        # evita error de KMeans si hay menos puntos que clusters
        n_clusters = max(1, len(vectors))

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(vectors)

    # setear cluster_id por lotes
    for pid, lab in zip(ids, labels):
        client.set_payload(
            collection_name=collection_name,
            payload={"cluster_id": int(lab)},
            points=[pid],
        )

    # conteos por cluster
    counts = [int((labels == i).sum()) for i in range(n_clusters)]
    return {
        "collection": collection_name,
        "n_clusters": int(n_clusters),
        "counts": counts,
    }


def calculate_centroids(collection_name: str) -> List[Dict[str, Any]]:
    """
    Calcula centroides por cluster usando los puntos etiquetados con cluster_id en payload.
    Devuelve una lista con {cluster_id, centroid, num_points}.
    """
    points = get_points_from_collection(collection_name, with_payload=True)
    if not points:
        return []

    # agrupar vectores por cluster_id
    by_cluster: Dict[int, List[List[float]]] = {}
    for p in points:
        payload = p.get("payload") or {}
        c = payload.get("cluster_id", None)
        if c is None:
            continue
        # cluster_id puede venir como numpy.int64
        try:
            cid = int(c)
        except Exception:
            continue

        vec = p.get("vector") or []
        if not vec:  # ignora vectores vacíos
            continue

        by_cluster.setdefault(cid, []).append(vec)

    results: List[Dict[str, Any]] = []
    for cid, vecs in by_cluster.items():
        arr = np.array(vecs, dtype=float)
        centroid = arr.mean(axis=0)
        results.append(
            {
                "cluster_id": int(cid),
                "centroid": centroid.tolist(),  # puro Python
                "num_points": int(arr.shape[0]),
            }
        )

    # orden opcional por cluster_id para estabilidad
    results.sort(key=lambda x: x["cluster_id"])
    return results


def create_collection_if_not_exists(collection_name: str, vector_size: int):
    cols = client.get_collections().collections
    exists = any(c.name == collection_name for c in cols)
    if not exists:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=int(vector_size), distance=models.Distance.COSINE
            ),
        )


def save_centroids(collection_name: str, centroids: list):
    """
    Guarda centroides en una colección separada en Qdrant.
    Si la colección no existe, la crea con el tamaño correcto.
    Incluye logs en puntos críticos para facilitar la depuración.
    """
    logger.info(f"🧭 Iniciando guardado de centroides para '{collection_name}'")

    # 1️⃣ Validar que haya centroides
    if not centroids or len(centroids) == 0:
        logger.warning(f"⚠️ No se recibieron centroides para '{collection_name}'.")
        return

    # 2️⃣ Verificar estructura de centroides
    try:
        vector_size = len(centroids[0]["centroid"])
        logger.debug(f"📏 Vector size detectado: {vector_size}")
    except Exception as e:
        logger.error(f"❌ Error leyendo tamaño de vector de centroides: {e}")
        return

    # 3️⃣ Nombre de la colección de centroides
    centroid_collection = f"{collection_name}_centroids"
    logger.debug(f"📛 Nombre de la colección destino: {centroid_collection}")

    # 4️⃣ Verificar existencia de la colección
    try:
        collections = client.get_collections().collections
        exists = any(c.name == centroid_collection for c in collections)
        logger.debug(f"🗂️ Colecciones existentes: {[c.name for c in collections]}")
    except Exception as e:
        logger.error(f"❌ Error obteniendo colecciones de Qdrant: {e}")
        return

    if not exists:
        try:
            logger.info(f"🆕 Creando colección '{centroid_collection}'...")
            client.recreate_collection(
                collection_name=centroid_collection,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"✅ Colección '{centroid_collection}' creada.")
        except Exception as e:
            logger.error(f"❌ Error creando colección '{centroid_collection}': {e}")
            return
    else:
        logger.info(f"ℹ️ Colección '{centroid_collection}' ya existe. Se actualizará.")

    # 5️⃣ Construcción de los puntos
    points = []
    try:
        for i, c in enumerate(centroids):
            # Asegurar conversión de numpy a lista si es necesario
            vector = c["centroid"]
            if hasattr(vector, "tolist"):
                vector = vector.tolist()

            point = models.PointStruct(
                id=int(i),
                vector=vector,
                payload={
                    "cluster_id": int(c["cluster_id"]),
                    "num_points": int(c["num_points"]),
                    "source_collection": collection_name
                }
            )
            points.append(point)
        logger.debug(f"📦 {len(points)} puntos listos para upsert en Qdrant.")
    except Exception as e:
        logger.error(f"❌ Error construyendo puntos de centroides: {e}")
        return

    # 6️⃣ Upsert en Qdrant
    try:
        client.upsert(
            collection_name=centroid_collection,
            points=points
        )
        logger.info(f"✅ {len(points)} centroides guardados en '{centroid_collection}'.")
    except Exception as e:
        logger.error(f"❌ Error guardando centroides en Qdrant: {e}")

    # 7️⃣ Log final
    logger.info(f"🏁 Finalizado guardado de centroides para '{collection_name}'")

def suggest_n_clusters(
    collection_name: str, k_min: int = 2, k_max: int = 12
) -> Dict[str, Any]:
    """
    Estima K óptimo (método del codo simplificado). Devuelve valores Python puros.
    """
    points = get_points_from_collection(collection_name, with_payload=False)
    if not points:
        return {"collection": collection_name, "suggested_k": 1, "scores": []}

    X = np.array([p["vector"] for p in points], dtype=float)
    km_scores: List[Tuple[int, float]] = []
    k_min = max(2, int(k_min))
    k_max = max(k_min, int(k_max), 3)
    k_max = min(k_max, len(X))  # no más clusters que puntos

    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X)
        km_scores.append((k, float(km.inertia_)))

    # escoger el de menor inercia (simple); puedes mejorar con "codo" real
    suggested = min(km_scores, key=lambda t: t[1])[0]
    return {
        "collection": collection_name,
        "suggested_k": int(suggested),
        "scores": [{"k": int(k), "inertia": float(inertia)} for k, inertia in km_scores],
    }