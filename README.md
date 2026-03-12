# AI Log Analyzer

AI Log Analyzer is a small AI-powered observability tool that analyzes application logs and generates human-readable summaries using a Large Language Model (LLM).

The system continuously collects logs, sends them to an LLM for analysis, stores the results in a database, and provides a web interface to inspect both the raw logs and the AI-generated insights.

This project demonstrates how LLMs can assist in log analysis, incident investigation, and operational monitoring.

---

# Features

• AI-powered log analysis using a Large Language Model (via Ollama)  
• FastAPI backend for log processing and API endpoints  
• SQLite database to store analysis history  
• Web interface to inspect logs and AI analysis results  
• Simulated service logs to demonstrate analysis capabilities  
• Docker-based multi-container architecture  

The AI generates structured outputs including:

• Summary of system behavior  
• Likely causes of issues  
• Suggested next steps  

---

# Architecture

The system consists of three main services:

### API (FastAPI)
Handles log ingestion, communicates with the LLM, stores analysis results in SQLite, and serves the web UI.

### Ollama (LLM Server)
Runs the language model responsible for analyzing the logs.

### Log Generator
Simulates application logs to demonstrate realistic operational scenarios.

Architecture flow:

User → FastAPI → Ollama → SQLite  
      ↑  
    Log Generator

---

# Tech Stack

Python  
FastAPI  
SQLAlchemy  
SQLite  
Jinja2 Templates  
Docker / Docker Compose  
Ollama (LLM runtime)  
HTTPX

---

# How It Works

1. The **log generator container** continuously produces simulated service logs.

2. The **FastAPI backend** reads the latest log entries from the log file.

3. The logs are sent to the **LLM via Ollama**.

4. The LLM analyzes the logs and produces a structured response including:
   - Summary
   - Likely causes
   - Suggested next steps

5. The result is stored in **SQLite**.

6. The **web UI** allows users to inspect analysis history and view detailed log analysis results.

---

## Learning Purpose

This project was developed as a learning exercise to explore:

- LLM-assisted log analysis
- backend development with FastAPI
- containerized system architecture using Docker
- integrating AI models into operational tools

Run:

```bash
docker compose up --build




