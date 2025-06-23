import os
import json
import numpy as np

from dotenv import load_dotenv
from pymilvus import connections, Collection


load_dotenv()

MILVUS_HOST = os.getenv('MILVUS_HOST')
MILVUS_PORT = os.getenv('MILVUS_PORT')

connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
info_col = Collection("product_information")
embed_col = Collection("product_embedding")
info_col.load()
embed_col.load()

def convert_to_json_safe(obj):
    if isinstance(obj, dict):
        return {k: convert_to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_safe(i) for i in obj]
    elif hasattr(obj, 'tolist'):  # numpy types
        return obj.tolist()
    elif isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    return obj

def get_products_by_ids(ids: list):
    if not ids:
        return []
    quoted_ids = [json.dumps(i) for i in ids]
    expr = f"id in [{', '.join(quoted_ids)}]"
    results = info_col.query(expr, output_fields=["*"])
    return [convert_to_json_safe(r) for r in results]

def search_by_image_vector(vector, top_k=10, ef=None):
    if ef is None or ef <= top_k:
        ef = max(64, top_k * 2)
    search_params = {"metric_type": "COSINE", "params": {"ef": ef}}
    results = embed_col.search(
        data=[vector],
        anns_field="image_embedding",
        param=search_params,
        limit=top_k,
        output_fields=["id"]
    )
    ids = [hit.entity.get("id") if hasattr(hit, "entity") else hit.id for hit in results[0]]
    return [{"id": i} for i in ids]

def get_combine_embeddings_by_ids(ids):
    # Hàm này giả sử trả về list (id, vector). Tùy implement của bạn (bạn cần sửa nếu khác).
    if not ids:
        return []
    quoted_ids = [json.dumps(i) for i in ids]
    expr = f"id in [{', '.join(quoted_ids)}]"
    results = embed_col.query(expr, output_fields=["id", "combine_embedding"])
    return [(r["id"], np.array(r["combine_embedding"], dtype=np.float32)) for r in results]
