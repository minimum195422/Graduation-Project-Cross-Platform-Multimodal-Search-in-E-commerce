# 🔄 Realtime Product Data Consumer with Multithreaded SQS, OpenCLIP, Milvus, and Elasticsearch

## 📌 Project Description

This project is a real-time data processing system designed to:

- **Consume product metadata from AWS SQS**
- **Download product images**
- **Extract multimodal embeddings using OpenCLIP (ViT-L-14-336)**
- **Store structured data into Milvus and Elasticsearch**
- **Maintain price and review history for product tracking**

It supports multithreaded execution to scale up consumption and processing throughput.

| File                   | Description                                            |
| ---------------------- | ------------------------------------------------------ |
| \`data_management.py\` | Core logic for consuming, processing, and storing data |
| \`thread_runner.py\`   | Multithreaded runner that launches multiple consumers  |
| \`.env\`               | Environment variables (not included, see below)        |

## ⚙️ Requirements

- Python 3.10+
- CUDA-enabled GPU (recommended)
- Dependencies:
  - \`torch\`, \`numpy\`, \`pillow\`, \`requests\`, \`open_clip_torch\`
  - \`boto3\`, \`python-dotenv\`, \`pymilvus\`, \`elasticsearch\`

Install all requirements:

\`\`\`bash
pip install -r requirements.txt
\`\`\`

## 🚀 How to Run

Start multithreaded workers (default: 10 threads):

\`\`\`bash
python thread_runner.py
\`\`\`

Each thread will:

- Fetch messages from the configured SQS queue
- Download and preprocess product image
- Compute embeddings using OpenCLIP
- Normalize and combine embeddings
- Upsert product data to Milvus and Elasticsearch
- Store price/review history

## 🧪 Example Output

On successful processing, the output will log:

\`\`\`bash
Using cuda
Loading OpenCLIP ViT-L-14-336
Thread 2 started consuming from SQS...
Thread 2 processed ID: abc123
\`\`\`

## 📌 Notes

- Make sure Milvus and Elasticsearch are up and running before starting the script.
- GPU is highly recommended for faster embedding generation.
- You can scale horizontally by launching this script on multiple machines.
  EOF
