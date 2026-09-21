# Digitano Builder - Backend Microservice

An autonomous multi-agent software engineering backend built with **FastAPI**, **AWS Bedrock**, **Google Gemini Flash**, and **Amazon DynamoDB**.

## Architecture
* **Framework:** FastAPI (Python 3.10+) with Server-Sent Events (SSE)
* **Primary Reasoning Engine:** AWS Bedrock (Claude 3.5 Sonnet / Amazon Nova Pro)
* **Failover Layer:** Google Gemini Flash API (Automated 429 throttling fallback)
* **Persistence:** Amazon DynamoDB (Single-Table Design)

## 7-Agent Sequential Pipeline
1. Product Owner
2. Software Analyst
3. UI Lead
4. Backend Lead
5. Full Stack Lead
6. Infrastructure Architect
7. Scrum Master

## Environment Variables
Create a `.env` file with:
```text
GEMINI_API_KEY=your_key
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_key
AWS_REGION=us-east-1
