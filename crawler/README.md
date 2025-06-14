# 🕷️ Crawler Configuration Guide

This project is a crawler that uses **RabbitMQ**, **AWS S3**, **AWS SQS**, and a headless browser powered by **Chrome + Chromedriver**.  
Before running the code, you need to set up your environment variables properly using a `.env` file.

---

## 📁 Step 1: Create `.env` File

Copy the example file provided:

```bash
cp .env.example .env
```

Then open `.env` in your preferred editor and fill in the necessary values.

---

## 🔧 Step 2: Configure Your Environment Variables

### ✅ RabbitMQ Configuration

| Variable            | Description                       |
| ------------------- | --------------------------------- |
| `RABBITMQ_HOST`     | Hostname or IP of RabbitMQ server |
| `RABBITMQ_VHOST`    | RabbitMQ virtual host             |
| `RABBITMQ_USER`     | RabbitMQ username                 |
| `RABBITMQ_PASSWORD` | RabbitMQ password                 |
| `MACHINE`           | Unique machine name (e.g., `PC1`) |

---

### ☁️ AWS S3 Configuration

| Variable         | Description                            |
| ---------------- | -------------------------------------- |
| `AWS_ACCESS_KEY` | AWS access key for S3                  |
| `AWS_SECRET_KEY` | AWS secret key for S3                  |
| `AWS_REGION`     | AWS region (default: `ap-southeast-1`) |
| `S3_BUCKET_NAME` | Name of your S3 bucket                 |

---

### 📬 AWS SQS Configuration

| Variable         | Description               |
| ---------------- | ------------------------- |
| `SQS_ACCESS_KEY` | AWS access key for SQS    |
| `SQS_SECRET_KEY` | AWS secret key for SQS    |
| `SQS_QUEUE_URL`  | Full URL of the SQS queue |

**Example:**

```env
SQS_QUEUE_URL=https://sqs.ap-southeast-1.amazonaws.com/123456789012/my-queue
```

---

## ▶️ Step 3: Run the Project

After filling in `.env`, you can start the crawler:

```bash
python main.py
```

Or if using Docker:

```bash
docker compose up --build
```

---

## 🛠 Dependencies

Ensure you have installed the required Python packages:

```bash
pip install -r requirements.txt
```