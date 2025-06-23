import os
import uuid
import json
import time
import requests
import torch
import numpy as np
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
from pymilvus import connections, Collection
from elasticsearch import Elasticsearch
import open_clip
import boto3

# Load ENV
load_dotenv()

sqs = boto3.client(
    'sqs',
    aws_access_key_id=os.getenv("SQS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("SQS_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION")
)
queue_url = os.getenv("SQS_QUEUE_URL")

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX = "products"

# Kết nối Milvus và Elasticsearch
connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
es = Elasticsearch(ES_HOST)
product_info = Collection("product_information")
product_embed = Collection("product_embedding")
price_history = Collection("product_price_history")
review_history = Collection("product_review_history")

# Load mô hình OpenCLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Sử dụng {device}")
print("Tải mô hình OpenClip ViT-L-14-336")
model, _, preprocess = open_clip.create_model_and_transforms(
    model_name="ViT-L-14-336", pretrained="openai", image_resolution=336
)
tokenizer = open_clip.get_tokenizer("ViT-L-14-336")
model.to(device)
model.eval()

def resize_image(img_bytes):
    image = Image.open(BytesIO(img_bytes)).convert("RGB")
    image = image.resize((336, 336), Image.BICUBIC)
    return preprocess(image).unsqueeze(0).to(device)

def clean_data(data):
    # Làm sạch giá trị
    price_str = data["price"].replace("₫", "").replace(",", "").replace(".", "").strip()
    data["price"] = float(price_str)
    data["rating"] = float(data["rating"])
    data["reviews_count"] = int(data["reviews_count"])
    ts = time.strptime(data["timestamp"], "%d%m%Y_%H%M%S")
    data["last_update"] = int(time.mktime(ts))
    return data

def insert_history(file_id, data):
    ts_int = data["last_update"]
    record_id = str(uuid.uuid4())
    dummy_vector = [0.0, 0.0]
    price_history.insert([
        [record_id],
        [file_id],
        [data["price"]],
        [ts_int],
        [dummy_vector]
    ])
    review_history.insert([
        [record_id],
        [file_id],
        [data["rating"]],
        [data["reviews_count"]],
        [ts_int],
        [dummy_vector]
    ])

def upsert_to_elasticsearch(file_id, data):
    doc = {
        "id": file_id,
        "product_name": data["name"]
    }
    es.index(index=ES_INDEX, id=file_id, document=doc)

# Hàm xóa embedding nếu đã tồn tại
def delete_embedding_if_exists(collection, id, partition=None):
    expr = f'id == "{id}"'
    collection.delete(expr, partition_name=partition)

def upsert_to_milvus(file_id, data, text_embedding, image_embedding, combined_embedding):
    dummy_vector = [0.0, 0.0]
    # Upsert product_info (nếu id trùng thì sẽ update)
    product_info.upsert([
        [file_id],
        [data["name"]],
        [data["store_url"]],
        [data["price"]],
        [data["rating"]],
        [data["reviews_count"]],
        [data["last_update"]],
        [data["image_url"]],
        [dummy_vector]
    ])

    # Xử lý upsert cho product_embed (xóa nếu đã tồn tại, rồi insert lại)
    # text_search
    delete_embedding_if_exists(product_embed, file_id, partition="text_search")
    product_embed.insert([
        [file_id],
        [text_embedding.tolist()],
        [image_embedding.tolist()],
        [combined_embedding.tolist()]
    ], partition_name="text_search")

    # image_search
    delete_embedding_if_exists(product_embed, file_id + "_img", partition="image_search")
    product_embed.insert([
        [file_id + "_img"],
        [text_embedding.tolist()],
        [image_embedding.tolist()],
        [combined_embedding.tolist()]
    ], partition_name="image_search")

    # combined_search
    delete_embedding_if_exists(product_embed, file_id + "_comb", partition="combined_search")
    product_embed.insert([
        [file_id + "_comb"],
        [text_embedding.tolist()],
        [image_embedding.tolist()],
        [combined_embedding.tolist()]
    ], partition_name="combined_search")

    insert_history(file_id, data)
    upsert_to_elasticsearch(file_id, data)

def receive_messages_from_sqs(max_messages=1, wait_time=5):
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=wait_time
    )
    return response.get("Messages", [])

def process_sqs_message(message, thread_id):
    try:
        body = json.loads(message["Body"])
        file_id = body.get("id", "").strip()
        if not file_id:
            print(f"❌ Bỏ qua message vì thiếu hoặc rỗng ID: {body}")
            return
        data = clean_data(body)
        img_response = requests.get(data["image_url"])
        image_input = resize_image(img_response.content)
        with torch.no_grad():
            image_embedding = model.encode_image(image_input).cpu().numpy()[0]
            text_input = tokenizer([data["name"]]).to(device)
            text_embedding = model.encode_text(text_input).cpu().numpy()[0]
        image_embedding /= np.linalg.norm(image_embedding)
        text_embedding /= np.linalg.norm(text_embedding)
        combined_embedding = (image_embedding + text_embedding) / 2
        combined_embedding /= np.linalg.norm(combined_embedding)
        upsert_to_milvus(file_id, data, text_embedding, image_embedding, combined_embedding)
        print(f"Thread {thread_id} đã xử lý ID: {file_id}")
        # Xoá message khỏi queue sau khi xử lý thành công
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message["ReceiptHandle"]
        )
    except Exception as e:
        print(f"Lỗi xử lý message: {e}")

def worker(thread_id):
    print(f"Thread {thread_id} bắt đầu tiêu thụ từ SQS...")
    while True:
        messages = receive_messages_from_sqs()
        if not messages:
            print(f"Thread {thread_id}: Không có message mới. Đợi 5s...")
            time.sleep(60)
            continue
        for msg in messages:
            print(f"Thread {thread_id}: Nhận message")
            process_sqs_message(msg, thread_id)
        time.sleep(1)

# if __name__ == "__main__":
#     print("Bắt đầu tiêu thụ dữ liệu từ SQS...")
#     while True:
#         messages = receive_messages_from_sqs()
#         if not messages:
#             print("Không có message mới. Đợi 5s...")
#             time.sleep(10)
#             continue
#         for msg in messages:
#             process_sqs_message(msg)
