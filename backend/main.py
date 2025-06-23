from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from PIL import Image
import io
import torch
import numpy as np

from fastapi.middleware.cors import CORSMiddleware
from model_loader import model, preprocess, tokenizer, device
from elastic_utils import search_product_ids_by_text
from milvus_utils import (
    get_products_by_ids,
    search_by_image_vector,
    get_combine_embeddings_by_ids
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search/text")
def search_text(q: str, limit: int = 50):
    ids = search_product_ids_by_text(q, size=limit)
    results = get_products_by_ids(ids)
    return {"results": results}

@app.post("/search/image")
async def search_image(file: UploadFile = File(...), limit: int = 50):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = model.encode_image(image_tensor)
        image_vector = image_features.cpu().numpy()[0].astype("float32")
    ids = search_by_image_vector(image_vector.tolist(), top_k=limit)
    id_list = [p["id"] for p in ids]
    results = get_products_by_ids(id_list)
    return {"results": results}

@app.post("/search/multimodal")
async def search_multimodal(q: str = Form(...), file: UploadFile = File(...), limit: int = 50):
    # 1. Text embedding
    with torch.no_grad():
        text_features = model.encode_text(tokenizer([q]).to(device))
        text_vector = text_features.cpu().numpy()[0].astype("float32")

    # 2. Image embedding
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = model.encode_image(image_tensor)
        image_vector = image_features.cpu().numpy()[0].astype("float32")

    # 3. Combine embedding (normalize)
    combined_vector = text_vector + image_vector
    combined_vector /= np.linalg.norm(combined_vector)

    # 4. Lấy danh sách ID từ text + ảnh
    ids_text = search_product_ids_by_text(q, size=limit*2)
    ids_image_dict = search_by_image_vector(image_vector.tolist(), top_k=limit*2)
    ids_image = [p["id"] for p in ids_image_dict]
    candidate_ids = list(set(ids_text + ids_image))

    # 5. Lấy combine_embedding của các ứng viên
    id_vec_pairs = get_combine_embeddings_by_ids(candidate_ids)

    # 6. Tính cosine similarity và xếp hạng
    def cosine_score(vec1, vec2):
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    scored = [(pid, cosine_score(combined_vector, vec)) for pid, vec in id_vec_pairs]
    top_ids = [pid for pid, _ in sorted(scored, key=lambda x: x[1], reverse=True)[:limit]]

    # 7. Lấy thông tin sản phẩm
    results = get_products_by_ids(top_ids)
    return {"results": results}
