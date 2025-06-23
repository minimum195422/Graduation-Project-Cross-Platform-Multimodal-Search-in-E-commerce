# 🔍 Multimodal Product Search API

This project is a **FastAPI-based backend** that allows users to search for e-commerce products by **text**, **image**, or a **combination of both**. It integrates **OpenCLIP** for embedding generation, **Elasticsearch** for text-based search, and **Milvus** for vector-based similarity retrieval.

## 🚀 API Endpoints

### 🔤 GET `/search/text`

Search products by text query.

**Parameters:**

| Name    | Type   | Required | Description                     |
| ------- | ------ | -------- | ------------------------------- |
| `q`     | string | ✅        | Text query                      |
| `limit` | int    | ❌        | Number of results (default: 50) |

**Example:**

```bash
GET /search/text?q=laptop
```

### 🖼️ POST `/search/image`

Search products by image similarity.

**Body (multipart/form-data):**

| Field   | Type | Required | Description       |
| ------- | ---- | -------- | ----------------- |
| `file`  | file | ✅        | Image file        |
| `limit` | int  | ❌        | Number of results |

**Example using curl:**

```bash
curl -X POST -F "file=@example.jpg" http://localhost:8000/search/image
```

### 🔀 POST `/search/multimodal`

Search products using both image and text.

**Body (multipart/form-data):**

| Field   | Type   | Required | Description       |
| ------- | ------ | -------- | ----------------- |
| `file`  | file   | ✅        | Image file        |
| `q`     | string | ✅        | Text query        |
| `limit` | int    | ❌        | Number of results |

**Example using curl:**

```bash
curl -X POST -F "file=@shoe.jpg" -F "q=red nike shoes" http://localhost:8000/search/multimodal
```

## ⚙️ Setup & Run

### 🔧 Install Dependencies

Make sure you are using Python 3.10+ and install requirements:

```bash
pip install -r requirements.txt
```

### 🔐 Environment Variables

Create a `.env` file (or copy from `.env.example`) with the following content:

```env
ES_HOST=http://localhost:9200
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### ▶️ Start the API Server

```bash
uvicorn main:app --reload
```

## 💡 Technology Stack

- FastAPI  
- OpenCLIP  
- Milvus  
- Elasticsearch  
- PIL, NumPy, PyTorch

## 📌 Notes

- This system assumes Milvus already contains precomputed embeddings.  
- The `/search/multimodal` endpoint uses late fusion and reranking with cosine similarity.
