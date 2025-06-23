# 🔍 Multimodal Product Search API

This project is a **FastAPI-based backend** that allows users to search for e-commerce products by **text**, **image**, or a **combination of both**. It integrates **OpenCLIP** for embedding generation, **Elasticsearch** for text-based search, and **Milvus** for vector-based similarity retrieval.

## 🚀 API Endpoints

### 🔤 GET `/search/text`

Search products by text query.

**Parameters:**

- \`q\` (string): Text query
- \`limit\` (int, default=50): Number of results

**Example:**
\`\`\`
GET /search/text?q=laptop
\`\`\`

### 🖼️ POST `/search/image`

Search products by image similarity.

**Body (multipart/form-data):**

- \`file\`: Image file
- \`limit\`: Number of results

**Example using curl:**
\`\`\`bash
curl -X POST -F "file=@example.jpg" http://localhost:8000/search/image
\`\`\`

### 🔀 POST `/search/multimodal`

Search products using both image and text.

**Body (multipart/form-data):**

- \`file\`: Image file
- \`q\`: Text query
- \`limit\`: Number of results

**Example:**
\`\`\`bash
curl -X POST -F "file=@shoe.jpg" -F "q=red nike shoes" http://localhost:8000/search/multimodal
\`\`\`

## ⚙️ Setup & Run

### 🔧 Install Dependencies

Make sure you are using Python 3.10+ and install requirements:

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 🔐 Environment Variables

Create a \`.env\` file (or use \`.env.example\`) with the following variables:

\`\`\`env
ES_HOST=http://localhost:9200
MILVUS_HOST=localhost
MILVUS_PORT=19530
\`\`\`

### ▶️ Start the API Server

\`\`\`bash
uvicorn main:app --reload
\`\`\`

## 💡 Technology Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenCLIP](https://github.com/mlfoundations/open_clip)
- [Milvus](https://milvus.io/)
- [Elasticsearch](https://www.elastic.co/elasticsearch/)
- [PIL](https://pillow.readthedocs.io/), NumPy, PyTorch

## 📌 Notes

- This system assumes Milvus already contains precomputed embeddings.
- The `/search/multimodal` endpoint uses late fusion and reranking with cosine similarity.
