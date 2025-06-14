## ⚙️ Step 1: Check GPU Compatibility

Ensure your system has an NVIDIA GPU with the correct drivers:

```bash
nvidia-smi
```

Then verify Docker can access your GPU:

```bash
docker run --rm --gpus all nvidia/cuda:12.0.0-base nvidia-smi
```

If this fails, install:

- [NVIDIA GPU Driver](https://www.nvidia.com/Download/index.aspx)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

---

## 🐳 Step 2: Start Milvus & Elasticsearch Backend

Use Docker Compose to start the full vector search stack:

```bash
docker compose up --build
```

### Services included:

| Service           | Ports       | Description                |
| ----------------- | ----------- | -------------------------- |
| Milvus Standalone | 19530, 9091 | Vector DB with GPU support |
| MinIO             | 9000, 9001  | Object storage for Milvus  |
| etcd              | internal    | Key-value store for Milvus |
| Elasticsearch     | 9200, 9300  | Full-text search engine    |

> ✅ Milvus version: `v2.5.12-gpu`  
> ✅ Elasticsearch version: `v8.12.0`

---

## 🩺 Step 3: Verify Service Health

Once all containers are running, check that the services are healthy:

- 🔗 Milvus: [http://localhost:9091/healthz](http://localhost:9091/healthz)
- 🔗 Elasticsearch: [http://localhost:9200](http://localhost:9200)
- 🔗 MinIO Console: [http://localhost:9001](http://localhost:9001)  
  *(Username: `minioadmin`, Password: `minioadmin`)*

---

## 🧱 Step 4: Initialize Collections and Indexes

Run your schema setup script to create Milvus collections and/or Elasticsearch indexes:

```bash
python create_collections.py
```

This script should handle:

- Creating Milvus collections (e.g., name, dimension, index type)
- Creating Elasticsearch indexes or mappings (if needed)

---
