BarbechAi
Enterprise-Grade AI CRM & Lead Generation Platform

BarbechAi is an intelligent, modular lead-generation and CRM platform designed to automate the discovery, enrichment, and management of business leads. Built for scalability, it leverages a split-stack architecture to handle intensive background tasks without compromising user experience.

🚀 Core Features
AI-Powered Lead Enrichment: Automated background processing to gather actionable intelligence on potential leads using real-time scraping techniques.

Split-Stack Architecture: Optimized performance using a FastAPI (Python) backend and a React-Vite (JavaScript) frontend.

Intelligent CRM: Robust data management with built-in logic to prevent duplicate entries and ensure data integrity.

Security & Auth: Secure route authentication to protect sensitive CRM data and operations.

CI/CD Ready: Streamlined deployment pipeline for continuous delivery.

🏗 System Architecture
The platform is designed around a four-role modular architecture:

Discovery Engine: Identifying and capturing raw lead data.

Enrichment Module: Async processing of lead details (via DuckDuckGo scraping).

Scoring System: Intelligent ranking of lead quality.

Agent Management: Task delegation for automated follow-ups.

🛠 Tech Stack
Backend: Python (FastAPI), PostgreSQL

Frontend: JavaScript (React-Vite)

Deployment: Vercel (Frontend/API), Render (Backend services)

📦 How to Run Locally
Prerequisites
Python 3.10+

Node.js 18+

PostgreSQL database

1. Setup Backend
Bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Set your DATABASE_URL in .env
uvicorn main:app --reload
2. Setup Frontend
Bash
cd frontend
npm install
npm run dev
📊 Deployment & Maintenance
Live App: barbech-ai.vercel.app

Monitoring: System uptime is actively monitored via UptimeRobot.

Deployment History: 44+ successful production deployments via integrated CI/CD.

💡 Status
Currently under active development. Recent focus includes background enrichment processing and stability patches for lead parsing.# BarbechAI
