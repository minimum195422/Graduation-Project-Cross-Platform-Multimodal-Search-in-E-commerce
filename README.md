# 🎓Graduation Project: Cross-Platform Multimodal Search in E-commerce

## 📘Introduction

In recent years, Vietnam’s e-commerce market has witnessed remarkable growth, becoming a driving force in the digital economy. By 2024, e-commerce accounted for 9% of total retail sales and nearly two-thirds of the digital economy's value, placing Vietnam among the top 10 fastest-growing e-commerce nations globally.

![Fastest Growing eCommerce Markets](assets/ecommerce_growth.jpg)

The convenience of online shopping—enabling users to search, compare, and purchase products across platforms—has reshaped consumer behavior. However, with over 400 registered e-commerce platforms in Vietnam and major players like Shopee, Lazada, Tiki, TikTok Shop, and Sendo, product information is highly fragmented. This fragmentation complicates the product discovery process, requiring users to manually switch between apps and compare offerings.

Existing price comparison tools (e.g., websosanh.vn) rely mainly on keyword-based search, which struggles with inconsistent naming, spelling errors, and vague queries. In addition, modern websites use dynamic loading techniques (AJAX, infinite scroll), making traditional crawling methods ineffective. Many platforms also implement anti-scraping measures such as CAPTCHA or rate limits.

To address these challenges, this project proposes an end-to-end system that automates data crawling, storage, and search across platforms. Selenium is used to simulate real user behavior, allowing robust data extraction from dynamic pages. Crawled data is indexed using both **Elasticsearch** (for keyword-based search) and **Milvus** (for image and vector similarity search). The system leverages **OpenCLIP**, a multimodal deep learning model, to support image-based and hybrid searches.

## 🛠️ Technologies Used

This project integrates multiple technologies and frameworks to build a scalable, efficient, and intelligent multi-platform product search system:

### ⚙️ Backend & Data Collection

- **Python 3.10** – Core language for backend logic and crawling pipelines
- **Selenium** – Browser automation to crawl dynamic web content (supports AJAX, lazy-loading, infinite scroll)
- **Requests** – Used for lightweight data fetching and HTML parsing (for static parts)

### 🗃️ Data Storage & Search

- **Elasticsearch** – Full-text search engine for structured product metadata
- **Milvus v2.5** – Vector database for fast similarity search (image/text embeddings)
- **AWS S3** – Cloud storage for product images and data archives

### 📩 Message Queues & Communication

- **Amazon SQS** – Distributed message queue for decoupling crawlers and processors
- **RabbitMQ** – Internal task queuing for scheduling and parallel processing

### 🤖 AI & Embedding

- **OpenCLIP (ViT-L/14 336px)** – Pre-trained vision-language model for generating multimodal embeddings
- **PyTorch** – Deep learning framework to run OpenCLIP model
- **Faiss (optional)** – For local vector similarity benchmarking

### 🌐 APIs & Integration

- **FastAPI** – Web framework for exposing search and admin endpoints
- **Uvicorn** – ASGI server for running FastAPI
- **Docker** – Containerization for deploying crawlers and services

### 📈 Monitoring & Evaluation

- **Elasticsearch Dashboards** – For search log analysis and indexing performance
- **Custom Metrics Logging** – For measuring crawling rate, product coverage, etc.

## 🧠 System Architecture

The system is designed as a distributed, message-driven pipeline that supports large-scale data collection, preprocessing, embedding, and search across multiple e-commerce platforms. It ensures scalability, modularity, and real-time responsiveness.

### 🧱 Architecture Overview

![Data Crawling Pipeline](assets/data_pipeline_diagram.jpg)

### 🔄 End-to-End Workflow

1. **Job Scheduling**
   
   - A centralized scheduler pushes crawl tasks into **RabbitMQ**.

2. **Crawling Layer**
   
   - Multiple **Crawler Servers** listen to RabbitMQ and process assigned jobs.
   - Using **Selenium**, they fetch product data (metadata + images) from dynamic e-commerce pages.
   - The raw data is stored in **AWS S3**.

3. **Task Trigger via SQS**
   
   - After uploading to S3, crawlers create a processing task in **AWS SQS** for downstream services.

4. **Data Processing & Indexing**
   
   - A **Data Management** module fetches raw data from S3.
   - Metadata is indexed into **Elasticsearch** for full-text search.
   - Images and text are encoded using **OpenCLIP**, and embeddings are stored in **Milvus**.

5. **Search & API Access**
   
   - A **FastAPI** service exposes:
     - Text Search (via Elasticsearch)
     - Image/Embedding Search (via Milvus)
     - Hybrid search (text + image fusion)
   - The user interface consumes this API for seamless cross-platform product discovery.

### ✅ System Highlights

- **Asynchronous Queuing** with RabbitMQ and SQS ensures robust task handling.
- **Separation of Concerns** allows crawling, processing, and search to scale independently.
- **Multimodal Search** enhances product matching via images and descriptions.
- **Cloud-native** components ensure flexibility, fault tolerance, and cost-effectiveness.

## 📜 License

This work is licensed under a [Creative Commons Attribution-NonCommercial 4.0 International License](https://creativecommons.org/licenses/by-nc/4.0/).

## 👤 Author & Contact

**Duong Binh Minh**  
Final-year Computer Engineering Student – VNU University of Engineering and Technology  
📫 Academic Email: [21020778@vnu.edu.vn](mailto:21020778@vnu.edu.vn)  
📫 Personal Email: [minimum.195422@gmail.com](mailto:minimum.195422@gmail.com)  
🎓 Supervisor: ThS. Trần Mạnh Cường