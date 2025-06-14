# pipelines.py
import os
import zipfile
import boto3
import json
from dotenv import load_dotenv

load_dotenv()

# Khởi tạo client S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION")
)

# SQS client
sqs_client = boto3.client(
    'sqs',
    aws_access_key_id=os.getenv("SQS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("SQS_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION")
)

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

def zip_folder(folder_path):
    """Tạo file zip từ folder và trả về đường dẫn zip"""
    if not os.path.exists(folder_path):
        print(f"❌ Folder không tồn tại: {folder_path}")
        return None

    zip_path = f"{folder_path}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, folder_path)
                zipf.write(full_path, arcname)
    return zip_path

def upload_file_to_s3(file_path, s3_path="archives/", crawler_name=None):
    s3_key = os.path.join(s3_path, os.path.basename(file_path))
    s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
    if crawler_name:
        print(f"📤 {crawler_name} Uploaded {file_path} to s3://{S3_BUCKET_NAME}/{s3_key}")
    else:
        print(f"📤 Uploaded {file_path} to s3://{S3_BUCKET_NAME}/{s3_key}")


def send_sqs_message_from_json(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        message_body = json.dumps(data, ensure_ascii=False)
        sqs_client.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=message_body)
        print(f"\U0001f4ac Sent SQS message for file: {json_path}")
    except Exception as e:
        print(f"❌ Lỗi gửi SQS message từ {json_path}: {e}")
