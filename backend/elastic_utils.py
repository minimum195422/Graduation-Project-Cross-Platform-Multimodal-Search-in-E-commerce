import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

ES_HOST = os.getenv('ES_HOST')
es = Elasticsearch(ES_HOST)
INDEX_NAME = "products"

def search_product_ids_by_text(query, size=10):
    body = {
        "query": {"match": {"product_name": query}},
        "size": size,
        "_source": ["id"]
    }
    res = es.search(index=INDEX_NAME, body=body)
    ids = [hit["_source"]["id"] for hit in res["hits"]["hits"]]
    return ids
