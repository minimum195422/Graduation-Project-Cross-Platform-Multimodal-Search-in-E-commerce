
import time
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
from pymilvus import (
    connections, FieldSchema, CollectionSchema, DataType, Collection, utility
)

load_dotenv()

ES_HOST = "http://localhost:9200"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

INDEX_NAME = "products"
TEXT_EMBED_DIM = 768
IMAGE_EMBED_DIM = 768
COMBINED_EMBED_DIM = 768
PARTITIONS = ["text_search", "image_search", "combined_search"]

def wait_for_elasticsearch(max_retries=20, wait_seconds=10):
    for i in range(max_retries):
        try:
            es = Elasticsearch(ES_HOST)
            if es.ping():
                print("✅ Elasticsearch đã sẵn sàng.")
                return es
        except Exception:
            time.sleep(wait_seconds)
    raise RuntimeError("❌ Không thể kết nối tới Elasticsearch.")

def wait_for_milvus(max_retries=20, wait_seconds=10):
    for i in range(max_retries):
        try:
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            if connections.has_connection("default"):
                print("✅ Milvus đã sẵn sàng.")
                return
        except Exception:
            time.sleep(wait_seconds)
    raise RuntimeError("❌ Không thể kết nối tới Milvus.")

def create_elasticsearch_index(es):
    if es.indices.exists(index=INDEX_NAME):
        print(f"⚠️ Chỉ mục '{INDEX_NAME}' đã tồn tại, đang xóa...")
        es.indices.delete(index=INDEX_NAME)

    index_settings = {
        "settings": {"number_of_shards": 2, "number_of_replicas": 1},
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "product_name": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {"keyword": {"type": "keyword"}}
                }
            }
        }
    }

    es.indices.create(index=INDEX_NAME, body=index_settings)
    print(f"✅ Tạo chỉ mục Elasticsearch '{INDEX_NAME}' thành công.")

def create_milvus_collections():
    collections = ["product_information", "product_embedding", "product_price_history", "product_review_history"]
    for name in collections:
        if utility.has_collection(name):
            print(f"⚠️ Collection '{name}' đã tồn tại, đang xóa...")
            utility.drop_collection(name)

    index_params_dummy = {
        "metric_type": "L2",
        "index_type": "FLAT",
        "params": {}
    }

    # product_information
    info_fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="product_name", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="url", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="price", dtype=DataType.FLOAT),
        FieldSchema(name="rating", dtype=DataType.FLOAT),
        FieldSchema(name="review_count", dtype=DataType.INT64),
        FieldSchema(name="last_update", dtype=DataType.INT64),
        FieldSchema(name="image_url", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="__dummy__", dtype=DataType.FLOAT_VECTOR, dim=2)
    ]
    info_schema = CollectionSchema(info_fields, description="Thông tin sản phẩm", enable_dynamic_field=False)
    info_collection = Collection(
        name="product_information",
        schema=info_schema,
        shards_num=8,
        consistency_level="Strong"
    )
    info_collection.create_index(field_name="__dummy__", index_params=index_params_dummy)
    print("✅ Tạo collection 'product_information' với index dummy")

    # product_embedding
    embed_fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="text_embedding", dtype=DataType.FLOAT_VECTOR, dim=TEXT_EMBED_DIM),
        FieldSchema(name="image_embedding", dtype=DataType.FLOAT_VECTOR, dim=IMAGE_EMBED_DIM),
        FieldSchema(name="combine_embedding", dtype=DataType.FLOAT_VECTOR, dim=COMBINED_EMBED_DIM)
    ]
    embed_schema = CollectionSchema(embed_fields, description="Embedding sản phẩm", enable_dynamic_field=False)
    embed_collection = Collection(
        name="product_embedding",
        schema=embed_schema,
        shards_num=8,
        consistency_level="Strong"
    )
    for p in PARTITIONS:
        embed_collection.create_partition(p)
    index_params = {"metric_type": "COSINE", "index_type": "HNSW", "params": {"M": 8, "efConstruction": 64}}
    for field in ["text_embedding", "image_embedding", "combine_embedding"]:
        embed_collection.create_index(field_name=field, index_params=index_params)
    embed_collection.release()
    print("✅ Tạo collection 'product_embedding' với index và partition")

    # product_price_history
    price_fields = [
        FieldSchema(name="record_id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="product_id", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="price", dtype=DataType.FLOAT),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="__dummy__", dtype=DataType.FLOAT_VECTOR, dim=2)
    ]
    price_schema = CollectionSchema(price_fields, description="Lịch sử giá", enable_dynamic_field=False)
    price_collection = Collection(
        name="product_price_history",
        schema=price_schema,
        shards_num=8,
        consistency_level="Strong"
    )
    price_collection.create_index(field_name="__dummy__", index_params=index_params_dummy)
    print("✅ Tạo collection 'product_price_history' với index dummy")

    # product_review_history
    review_fields = [
        FieldSchema(name="record_id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="product_id", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="rating", dtype=DataType.FLOAT),
        FieldSchema(name="review_count", dtype=DataType.INT64),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="__dummy__", dtype=DataType.FLOAT_VECTOR, dim=2)
    ]
    review_schema = CollectionSchema(review_fields, description="Lịch sử đánh giá", enable_dynamic_field=False)
    review_collection = Collection(
        name="product_review_history",
        schema=review_schema,
        shards_num=8,
        consistency_level="Strong"
    )
    review_collection.create_index(field_name="__dummy__", index_params=index_params_dummy)
    print("✅ Tạo collection 'product_review_history' với index dummy")


if __name__ == "__main__":
    print("🚀 Bắt đầu khởi tạo hệ thống lưu trữ...")
    es = wait_for_elasticsearch()
    wait_for_milvus()
    create_elasticsearch_index(es)
    create_milvus_collections()
    print("✅ HOÀN TẤT KHỞI TẠO STORAGE")