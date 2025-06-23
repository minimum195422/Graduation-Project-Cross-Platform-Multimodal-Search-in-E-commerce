cat <<EOF > README.md

# 🔍 Multimodal Product Search API

This project is a **FastAPI-based backend** that allows users to search for e-commerce products by **text**, **image**, or a **combination of both**. It integrates **OpenCLIP** for embedding generation, **Elasticsearch** for text-based search, and **Milvus** for vector-based similarity retrieval.

---

## 🧱 System Architecture

\`\`\`mermaid
flowchart TD
    A[Client Request] --> B[FastAPI Backend]
    B --> C[OpenCLIP Embedding]
    C --> D[Text Search → Elasticsearch]
    C --> E[Image/Vector Search → Milvus]
    D --> F[Product ID List]
    E --> F
    F --> G[Join & Rank]
    G --> H[Return Top Products]
\`\`\`

---

## 📂 Project Structure

| File                 | Purpose                                                  |
| -------------------- | -------------------------------------------------------- |
| \`main.py\`          | FastAPI app with search routes (text, image, multimodal) |
| \`model_loader.py\`  | Load OpenCLIP model, tokenizer, preprocess functions     |
| \`elastic_utils.py\` | Elasticsearch text search logic                          |
| \`milvus_utils.py\`  | Milvus-based vector search and data retrieval            |

---

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

---

### 🖼️ POST `/search/image`

Search products by image similarity.

**Body (multipart/form-data):**

- \`file\`: Image file
- \`limit\`: Number of results

**Example using curl:**
\`\`\`bash
curl -X POST -F "file=@example.jpg" http://localhost:8000/search/image
\`\`\`

---

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

---

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

---

## 💡 Technology Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenCLIP](https://github.com/mlfoundations/open_clip)
- [Milvus](https://milvus.io/)
- [Elasticsearch](https://www.elastic.co/elasticsearch/)
- [PIL](https://pillow.readthedocs.io/), NumPy, PyTorch

---

## 📌 Notes

- This system assumes Milvus already contains precomputed embeddings.
- The `/search/multimodal` endpoint uses late fusion and reranking with cosine similarity.

---

## 🧪 Example Response

\`\`\`json
{
  "results": [
    {
      "id": "abc123",
      "product_name": "Red Nike Running Shoes",
      "price": 1290000,
      "rating": 4.7,
      "reviews_count": 512,
      "image_url": "https://cdn.example.com/img/abc123.jpg"
    },
    ...
  ]
}
\`\`\`

EOF
